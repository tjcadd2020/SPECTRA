import pandas as pd
import numpy as np
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
import shap 
from imblearn.over_sampling import SMOTE
import pickle

from sklearn import metrics
#####################################
######### resample with SMOTE #######
#####################################
def smote_resample_one_vs_rest(X,Yohe,target_phenotype):
    Y = Yohe.idxmax(axis = 1)
    class_counts = Y.value_counts()
    if (class_counts < 2).any():
        raise ValueError(f"Some classes have fewer than 2 samples in resampling for {target_phenotype}.")
    negative_class_counts = class_counts.drop(index=target_phenotype, errors='ignore')
    if negative_class_counts.empty:
        raise ValueError(f"No negative classes present when resampling for {target_phenotype}.")

    max_negative_count = negative_class_counts.max()
    negative_class_n = len(negative_class_counts)
    
    positive_target = negative_class_n  * max_negative_count
    negative_target = max_negative_count
    
    sampling_strategy = {}
    for p, count in class_counts.items():
        if p == target_phenotype:
            sampling_strategy[p] = positive_target
        else:
            sampling_strategy[p] = negative_target

    oversample = SMOTE(sampling_strategy=sampling_strategy, random_state=1)
    X_resample, Y_resample = oversample.fit_resample(X, Y)    
    Y_resample_ohe = pd.get_dummies(Y_resample)

    return X_resample, Y_resample_ohe

#####################################
############### get MRI #############
#####################################
def train_MRI_classifier(TrainX,TrainY):
    cf = RandomForestClassifier(oob_score=True, class_weight='balanced', random_state=42,n_jobs=-1)
    cf.fit(TrainX, TrainY)
    return cf

def predict_MRI_for_phenotype(MRIcf,Abundance,p):
    pred_MRI = MRIcf.predict_proba(Abundance)[:, 1]
    MRI_df = pd.DataFrame(pred_MRI,index=Abundance.index,columns=[p])
    return MRI_df

def compute_MRI_CV_all_phenotypes(MSigPath,X_train,Y_train,phenotypes):
    cv_MRI_df = pd.DataFrame()
    for p in phenotypes:
        MSigsName_file = os.path.join(MSigPath,f'MSigs_{p}.csv')
        MSigsName = pd.read_csv(MSigsName_file,index_col = 0)
        MSigs = MSigsName[f'MSig({p})']
        X_train_Msigs = X_train.loc[:,MSigs]
        inner_cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
        cv_MRI_p_df = pd.DataFrame()

        for fold,(train_idx, val_idx) in enumerate(inner_cv.split(X_train_Msigs, Y_train),start =1):

            X_train_fold, X_val_fold = X_train_Msigs.iloc[train_idx], X_train_Msigs.iloc[val_idx]
            Y_train_fold, Y_val_fold = Y_train.iloc[train_idx], Y_train.iloc[val_idx]
            if p not in Y_train_fold['phenotype'].unique():
                continue
            Y_train_Ohe = pd.get_dummies(Y_train_fold['phenotype'])
            X_resample, Y_resample_ohe = smote_resample_one_vs_rest(X_train_fold,Y_train_Ohe,p)
            #getMRI classifier
            MRIcf = train_MRI_classifier(X_resample,Y_resample_ohe[f'{p}'])
            #getMRI
            predicted_MRI = predict_MRI_for_phenotype(MRIcf,X_val_fold,p)
            cv_MRI_p_df = pd.concat([cv_MRI_p_df,predicted_MRI],axis = 0)
        cv_MRI_df = pd.concat([cv_MRI_df,cv_MRI_p_df],axis = 1)
    return cv_MRI_df

def train_and_save_MRI_classifiers(MSigPath,X_train,Y_train,phenotypes,save_MRIcf_path):
    for p in phenotypes:
        MSigsName_file = os.path.join(MSigPath,f'MSigs_{p}.csv')
        MSigsName = pd.read_csv(MSigsName_file,index_col = 0)
        MSigs = MSigsName[f'MSig({p})']
        X_train_Msigs = X_train.loc[:,MSigs]
        Y_train_Ohe = pd.get_dummies(Y_train['phenotype'])
        X_resample, Y_resample_ohe = smote_resample_one_vs_rest(X_train_Msigs,Y_train_Ohe,p)
        MRIcf = train_MRI_classifier(X_resample,Y_resample_ohe[p])
        MRIcf_file = os.path.join(save_MRIcf_path,f'MRIfor{p}.pkl')
        with open(MRIcf_file, "wb") as f:
            pickle.dump(MRIcf, f)
            print(f'Saved MRI classifier for {p}!')

def load_MRIcf_and_predict_all_phenotypes(MRIcf_path,Abundance,phenotypes):
    MRI_res = pd.DataFrame()
    for p in phenotypes:
        MRIcf_file = os.path.join(MRIcf_path,f'MRIfor{p}.pkl')
        with open(MRIcf_file, "rb") as f:
            MRIcf = pickle.load(f)
        MSigs_names = MRIcf.feature_names_in_
        Abundance_Msigs = Abundance.reindex(columns=MSigs_names, fill_value=0)
        pred_MRI= predict_MRI_for_phenotype(MRIcf,Abundance_Msigs,p)
        MRI_res = pd.concat([MRI_res,pred_MRI],axis = 1)
    return MRI_res

#####################################
######### SPECTRA model #############
#####################################          
def train_SPECTRA_Models(TrainX,TrainY):
    model = RandomForestClassifier(oob_score=True, class_weight='balanced', random_state=42,n_jobs=-1)
    model.fit(TrainX,TrainY)
    return model

def predict_SPECTRA_for_phenotype(SPECTRAmodel,MRIfile):
    pred_SPECTRA = SPECTRAmodel.predict_proba(MRIfile)
    SPECTRA_df = pd.DataFrame(pred_SPECTRA,index=MRIfile.index,columns=SPECTRAmodel.classes_)
    return SPECTRA_df

def compute_SPECTRA_CV_all_phenotypes(X_train,Y_train):
    cv_SPECTRA_df = pd.DataFrame(index=X_train.index)
    
    inner_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    for fold,(train_idx, val_idx) in enumerate(inner_cv.split(X_train, Y_train['phenotype']),start =1):
        X_train_fold, X_val_fold = X_train.iloc[train_idx], X_train.iloc[val_idx]
        Y_train_fold, Y_val_fold = Y_train.iloc[train_idx], Y_train.iloc[val_idx]
        #get SPECTRA model
        SPECTRA_model = train_SPECTRA_Models(X_train_fold,Y_train_fold['phenotype'])
        #SPECTRA prediction
        prediction = predict_SPECTRA_for_phenotype(SPECTRA_model,X_val_fold)
        cv_SPECTRA_df.loc[X_val_fold.index, SPECTRA_model.classes_] = prediction.values
    return cv_SPECTRA_df

def train_and_save_SPECTRA_models(TrainX,TrainY,save_model_path):
    model = train_SPECTRA_Models(TrainX,TrainY['phenotype'])
    save_model_file = os.path.join(save_model_path,f'SPECTRA.pkl')
    with open(save_model_file, "wb") as f:
        pickle.dump(model, f)

def load_and_predict_SPECTRA_for_phenotype(model_path,MRIfile,phenotypes,explain=True):

    model_file = os.path.join(model_path,f'SPECTRA.pkl')
    with open(model_file, "rb") as f:
        model = pickle.load(f)
    MRIfile = MRIfile.loc[:,model.feature_names_in_]

    prediction =pd.DataFrame(model.predict_proba(MRIfile),index=MRIfile.index,columns=model.classes_)
    if explain:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(MRIfile)

    return prediction,explainer

#####################################
############### score  ##############
#####################################

def true_positive(y_true, y_pred):
    tp = 0 
    for yt, yp in zip(y_true, y_pred):      
        if yt == 1 and yp == 1:
            tp += 1 
    return tp

def true_negative(y_true, y_pred):  
    tn = 0 
    for yt, yp in zip(y_true, y_pred): 
        if yt == 0 and yp == 0:
            tn += 1      
    return tn

def false_positive(y_true, y_pred): 
    fp = 0
    for yt, yp in zip(y_true, y_pred):
        if yt == 0 and yp == 1:
            fp += 1 
    return fp

def false_negative(y_true, y_pred):
    fn = 0
    for yt, yp in zip(y_true, y_pred):
        if yt == 1 and yp == 0:
            fn += 1
    return fn

def weighted_tpr(y_true,y_pred):
    total_samples = len(y_true)
    weighted_tpr_sum = 0
    for class_ in list(y_true.unique()):
        temp_true = [1 if p == class_ else 0 for p in y_true]
        temp_pred = [1 if p == class_ else 0 for p in y_pred]
        tp = true_positive(temp_true, temp_pred)
        fn = false_negative(temp_true, temp_pred)
        temp_tpr = tp / (tp + fn +1e-6)
        support = sum(temp_true)
        weighted_tpr_sum += temp_tpr * support
        print(class_)
        print(temp_tpr)
    weighted_tpr_sum /= total_samples
    return weighted_tpr_sum

def weighted_tnr(y_true,y_pred):
    total_samples = len(y_true)
    weighted_tnr_sum = 0
    for class_ in list(y_true.unique()):
        temp_true = [1 if p == class_ else 0 for p in y_true]
        temp_pred = [1 if p == class_ else 0 for p in y_pred]
        tn = true_negative(temp_true, temp_pred)
        fp = false_positive(temp_true, temp_pred)
        temp_tnr = tn / (tn + fp +1e-6)
        support = sum(temp_true)
        weighted_tnr_sum += temp_tnr * support
        print(class_)
        print(temp_tnr)
    weighted_tnr_sum /= total_samples
    return weighted_tnr_sum

def weighted_npv(y_true,y_pred):
    total_samples = len(y_true)
    weighted_npv_sum = 0
    for class_ in list(y_true.unique()):
        temp_true = [1 if p == class_ else 0 for p in y_true]
        temp_pred = [1 if p == class_ else 0 for p in y_pred]
        tn = true_negative(temp_true, temp_pred)
        fn = false_negative(temp_true, temp_pred)
        temp_npv = tn / (tn + fn +1e-6)
        support = sum(temp_true)
        weighted_npv_sum += temp_npv * support
    weighted_npv_sum /= total_samples
    return weighted_npv_sum

def weighted_macro_precision(y_true, y_pred):
    total_samples = len(y_true)
    weighted_precision_sum = 0
    # loop over all classes
    for class_ in list(y_true.unique()):
        # all classes except current are considered negative
        temp_true = [1 if p == class_ else 0 for p in y_true]
        temp_pred = [1 if p == class_ else 0 for p in y_pred]
        # compute true positive for current class
        tp = true_positive(temp_true, temp_pred)
        # compute false positive for current class
        fp = false_positive(temp_true, temp_pred)
        # compute precision for current class
        temp_precision = tp / (tp + fp + 1e-6)
        support = sum(temp_true)
        weighted_precision_sum += temp_precision * support
    # calculate and return average precision over all classes
    weighted_precision_sum /= total_samples
    return weighted_precision_sum

def weighted_macro_f1(y_true, y_pred):
    total_samples = len(y_true)
    weighted_f1 = 0
    # loop over all classes
    for class_ in list(y_true.unique()):
        # all classes except current are considered negative
        temp_true = [1 if p == class_ else 0 for p in y_true]
        temp_pred = [1 if p == class_ else 0 for p in y_pred]
        # compute true positive for current class
        tp = true_positive(temp_true, temp_pred)
        # compute false negative for current class
        fn = false_negative(temp_true, temp_pred)
        # compute false positive for current class
        fp = false_positive(temp_true, temp_pred)
        # compute recall for current class
        temp_recall = tp / (tp + fn + 1e-6)
        # compute precision for current class
        temp_precision = tp / (tp + fp + 1e-6)
        temp_f1 = 2 * temp_precision * temp_recall / (temp_precision + temp_recall + 1e-6)
        support = sum(temp_true)
        # keep adding f1 score for all classes
        weighted_f1 += temp_f1 * support
    # calculate and return average f1 score over all classes
    weighted_f1 /= total_samples
    return weighted_f1

def weighted_fpr(y_true,y_pred):
    total_samples = len(y_true)
    weighted_fpr_sum = 0
    for class_ in list(y_true.unique()):
        temp_true = [1 if p == class_ else 0 for p in y_true]
        temp_pred = [1 if p == class_ else 0 for p in y_pred]
        fp = false_positive(temp_true, temp_pred)
        tn = true_negative(temp_true, temp_pred)
        temp_fpr = fp / (fp + tn +1e-6)
        support = sum(temp_true)
        weighted_fpr_sum += temp_fpr * support
        print(class_)
        print(temp_fpr)
    weighted_fpr_sum /= total_samples
    return weighted_fpr_sum
