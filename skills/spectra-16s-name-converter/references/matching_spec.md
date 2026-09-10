# Matching specification

This document is the deterministic contract used by the model-only Skill. It contains no biological synonym mapping.

## 1. Standard identity

For each row in `MSigs.csv`:

```text
Msig = the exact output label
Species = standard species text
genus_key = casefold(first taxonomic word after removing brackets used only as formatting)
species_key = casefold(the remaining species text, with whitespace collapsed)
```

Examples:

| Standard species | genus key | species key |
|---|---|---|
| `Pseudomonas mendocina` | `pseudomonas` | `mendocina` |
| `[Clostridium] cocleatum` | `clostridium` | `cocleatum` |
| `Rahnella sp. Y9602` | `rahnella` | `sp. y9602` |

Square brackets in a reference genus are ignored only for the character-level comparison. They do not create an alias to another genus. Thus `[Eubacterium] siraeum` can match `Eubacterium siraeum` or `g__[Eubacterium];s__siraeum`, but it cannot match `Ruminiclostridium siraeum`.

## 2. Explicit lineage parsing

Split on semicolons and parse fields matching `rank__value`. Keep `g__` and `s__`; ignore the other ranks for species matching. Empty placeholders (`g__`, `s__`, `__`, blank, `NA`, `unknown`, and similar) carry no evidence.

For a complete `g__`/`s__` pair, do not compare the full lineage string with `MSigs.csv`. Apply this structured transformation:

1. `genus = base(first token of g__ value)`, where `base` removes outer brackets and everything after the first underscore.
2. `species = s__ value` with whitespace collapsed.
3. If the first token of `species` has the same `base` genus, remove that token.
4. Match the resulting genus and complete species designation against the reference `Species` identity.

This is the critical transformation for annotated lineages such as `g__Gemmiger_A_73129;s__Gemmiger_A_73129 formicilis`. It yields `(Gemmiger, formicilis)`, not a literal species string containing the annotation.

Examples:

```text
g__Pseudomonas;s__mendocina
=> genus=Pseudomonas, species=mendocina

g__Campylobacter_B;s__Campylobacter_B hominis
=> genus=Campylobacter_B, species=Campylobacter_B hominis
=> genus key=campylobacter, species key=hominis

g__Akkermansia;s__muciniphila
=> genus=Akkermansia, species=muciniphila
```

Regression pairs from the supplied Test2 table:

```text
g__Campylobacter_B;s__Campylobacter_B hominis
=> 76517_Campylobacter hominis

g__Gemmiger_A_73129;s__Gemmiger_A_73129 formicilis
=> 745368_Gemmiger formicilis

g__Clostridium_A_51961;s__Clostridium_A_51961 leptum
=> 1535_[Clostridium] leptum

g__Streptococcus;s__Streptococcus vestibularis
=> 1343_Streptococcus vestibularis

g__Acidaminococcus;s__Acidaminococcus   intestini
=> 187327_Acidaminococcus intestini

g__Alistipes_A_871400;s__Alistipes_A_871400 onderdonkii
=> 328813_Alistipes onderdonkii

g__Parabacteroides_B_862066;s__Parabacteroides_B_862066 merdae
=> 46503_Parabacteroides merdae

g__Odoribacter_865974;s__Odoribacter splanchnicus
=> 28118_Odoribacter splanchnicus
```

If `g__` is empty but `s__` is a complete binomial name, parse the `s__` value as an ordinary label. If it is only an epithet, do not guess the missing genus.

### Rankless positional paths

Some inputs have no rank prefixes and instead use positional semicolon fields:

```text
Bacteria;Bacteroidetes;Bacteroidia;Bacteroidales;Bacteroidaceae;Bacteroides;Bacteroides stercoris
```

For a path with at least six fields and no rank prefixes, treat the final two fields as genus and species. The earlier fields are context only. When the final field is a complete binomial, including a bracketed binomial, parse that final field directly as the species identity. When it is only an epithet, combine it with the preceding genus field.

Examples:

```text
...;Bacteroides;Bacteroides stercoris
=> 46506_Bacteroides stercoris

...;Eubacterium;[Eubacterium] hallii
=> unmatched with the bundled MSigs.csv because hallii is absent

...;Ruminiclostridium;[Eubacterium] siraeum
=> 39492_[Eubacterium] siraeum
```

The third example uses the explicit full label in the final field. It is not an epithet-only cross-genus match. By contrast, `g__Ruminiclostridium_E;s__Ruminiclostridium_E siraeum` remains unmatched against `[Eubacterium] siraeum` because both explicit lineage fields name `Ruminiclostridium`.

## 3. Ordinary labels and split columns

For an ordinary label, consider these exact interpretations:

1. first token is genus and remaining whitespace-delimited text is species;
2. first token is `Genus_species`, with the first underscore separating genus and species;
3. first token is `Genus_ANNOTATION` followed by a whitespace species, where the underscore part is a genus annotation and is discarded;
4. bracketed genus followed by species.

When more than one interpretation is possible, retain all exact candidates and select only a unique best reference identity. This is what lets `Bacteroides_vulgatus` work while also letting `Campylobacter_B hominis` discard `_B` from the genus. Discarding `_B` is allowed only because the base genus remains `Campylobacter`; it must never turn `Ruminiclostridium_E` into `Eubacterium`.

For split columns, combine genus and species fields before matching. Do not use abundance, count, sample, or arbitrary numeric ID columns as taxon evidence.

## 4. Safe annotation stripping

Annotation stripping is constrained to boundaries and is never an edit-distance match.

- Genus: `Campylobacter_B` → `Campylobacter`; `Sphingomonas_L_486704` → `Sphingomonas`.
- Species with a repeated genus: `Campylobacter_B hominis` → `hominis` after the genus has been identified.
- Trailing species metadata is optional and conservative: `muciniphila_D_776786` can yield `muciniphila` because the suffix contains uppercase/digits and is attached by `_`. A different lowercase species word is not removed automatically.

The reference genus and species must still both agree. Therefore a genus-only input such as `Bifidobacterium_UC` remains unmatched.

## 5. Bracketed reference examples

The following cases must be handled exactly:

```text
MSigs Species: [Eubacterium] siraeum
Input: Eubacterium siraeum
=> 39492_[Eubacterium] siraeum

MSigs Species: [Clostridium] leptum
Input: g__Clostridium_A;s__Clostridium_A leptum
=> 1535_[Clostridium] leptum

MSigs Species: [Eubacterium] siraeum
Input: g__Ruminiclostridium_E;s__Ruminiclostridium_E siraeum
=> Unmatched_taxon_N
```

The last result is required. Same-species-epithet evidence is insufficient when the normalized genera differ.

## 6. Output invariant

Output rows are generated one-for-one in input order. For each row:

```text
Original taxon label = selected raw label
Corresponding Msig   = exact reference Msig, or next Unmatched_taxon_N
```

The helper writes a blank-headed CSV index column so the output has a stable row index while its data columns remain exactly the two required columns.
