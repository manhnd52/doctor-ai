CREATE FULLTEXT INDEX label_name_ft
FOR (n:
  disease |
  exposure |
  anatomy |
  biological_process |
  approval_status |
  pathway |
  effect_or_phenotype |
  cellular_component |
  category |
  gene_or_protein |
  molecular_function |
  drug
)
ON EACH [n.name]
OPTIONS {
  indexConfig: {
    `fulltext.analyzer`: 'english',
    `fulltext.eventually_consistent`: true 
  }
};
