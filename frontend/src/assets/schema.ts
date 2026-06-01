// schema.ts

export const schema = {
    labels: [
        {
            id: "Disease",
            name: "Disease",
            color: "#F77E7E",
            description: "Pathological condition of a part, organ, or system of an organism.",
            properties: [
                { name: "id", type: "string" },
                { name: "name", type: "string" },
                { name: "source", type: "string" },
                { name: "prevalence", type: "string" },
                { name: "epidemiology", type: "string" },
                { name: "management_and_treatment", type: "string" },
                { name: "causes", type: "string" },
                { name: "risk_factors", type: "string" },
                { name: "complications", type: "string" },
                { name: "prevention", type: "string" },
                { name: "when_to_see_a_doctor", type: "string" },
                { name: "description", type: "string" },
                { name: "index", type: "integer" }
            ]
        },
        {
            id: "Exposure",
            name: "Exposure",
            color: "#F5D323",
            description: "An environmental or chemical agent to which an organism is subjected.",
            properties: [
                { name: "id", type: "string" },
                { name: "name", type: "string" },
                { name: "source", type: "string" },
                { name: "index", type: "integer" }
            ]
        },
        {
            id: "Anatomy",
            name: "Anatomy",
            color: "#7ED321",
            description: "Structural body parts, tissues, or organs.",
            properties: [
                { name: "id", type: "string" },
                { name: "name", type: "string" },
                { name: "source", type: "string" },
                { name: "index", type: "integer" }
            ]
        },
        {
            id: "BiologicalProcess",
            name: "Biological Process",
            color: "#50E3C2",
            description: "Biological processes or series of events.",
            properties: [
                { name: "id", type: "string" },
                { name: "name", type: "string" },
                { name: "source", type: "string" },
                { name: "index", type: "integer" }
            ]
        },
        {
            id: "ApprovalStatus",
            name: "Approval Status",
            color: "#9013FE",
            description: "Regulatory approval status of a substance.",
            properties: [
                { name: "name", type: "string" },
                { name: "index", type: "integer" }
            ]
        },
        {
            id: "Pathway",
            name: "Pathway",
            color: "#B8E986",
            description: "Biological pathway of molecular interactions.",
            properties: [
                { name: "id", type: "string" },
                { name: "name", type: "string" },
                { name: "source", type: "string" },
                { name: "index", type: "integer" }
            ]
        },
        {
            id: "EffectOrPhenotype",
            name: "Effect or Phenotype",
            color: "#E6B8AF",
            description: "Observed physical, biochemical or physiological characteristics.",
            properties: [
                { name: "id", type: "string" },
                { name: "name", type: "string" },
                { name: "source", type: "string" },
                { name: "index", type: "integer" }
            ]
        },
        {
            id: "CellularComponent",
            name: "Cellular Component",
            color: "#7A7A7A",
            description: "Subcellular structures, locations, and macromolecular complexes.",
            properties: [
                { name: "id", type: "string" },
                { name: "name", type: "string" },
                { name: "source", type: "string" },
                { name: "index", type: "integer" }
            ]
        },
        {
            id: "Category",
            name: "Category",
            color: "#BD10E0",
            description: "Classification category for substances.",
            properties: [
                { name: "name", type: "string" },
                { name: "index", type: "integer" }
            ]
        },
        {
            id: "GeneOrProtein",
            name: "Gene or Protein",
            color: "#4A90E2",
            description: "Basic unit of heredity or the functional protein product.",
            properties: [
                { name: "id", type: "string" },
                { name: "name", type: "string" },
                { name: "source", type: "string" },
                { name: "index", type: "integer" }
            ]
        },
        {
            id: "MolecularFunction",
            name: "Molecular Function",
            color: "#54E6F6",
            description: "Elemental activities of a gene product at the molecular level.",
            properties: [
                { name: "id", type: "string" },
                { name: "name", type: "string" },
                { name: "source", type: "string" },
                { name: "index", type: "integer" }
            ]
        },
        {
            id: "Drug",
            name: "Drug",
            color: "#F5A623",
            description: "Chemical substance used to treat, cure, prevent, or diagnose a disease.",
            properties: [
                { name: "id", type: "string" },
                { name: "name", type: "string" },
                { name: "source", type: "string" },
                { name: "description", type: "string" },
                { name: "half_life", type: "string" },
                { name: "mechanism_of_action", type: "string" },
                { name: "pharmacodynamics", type: "string" },
                { name: "aggregate_state", type: "string" },
                { name: "index", type: "integer" },
                { name: "molecular_weight", type: "float" },
                { name: "tpsa", type: "float" },
                { name: "clogp", type: "float" }
            ]
        }
    ],

    relationships: [
        { name: "PHENOTYPE_PRESENT", source: "Disease", target: "EffectOrPhenotype", properties: [] },
        { name: "ASSOCIATED_WITH", source: "Disease", target: "GeneOrProtein", properties: [] },
        { name: "PARENT_CHILD", source: "Disease", target: "Disease", properties: [] },
        { name: "PHENOTYPE_ABSENT", source: "Disease", target: "EffectOrPhenotype", properties: [] },
        { name: "LINKED_TO", source: "Disease", target: "Exposure", properties: [] },
        { name: "INTERACTS_WITH", source: "Exposure", target: "GeneOrProtein", properties: [] },
        { name: "INTERACTS_WITH", source: "Exposure", target: "BiologicalProcess", properties: [] },
        { name: "INTERACTS_WITH", source: "Exposure", target: "CellularComponent", properties: [] },
        { name: "INTERACTS_WITH", source: "Exposure", target: "MolecularFunction", properties: [] },
        { name: "PARENT_CHILD", source: "Exposure", target: "Exposure", properties: [] },
        { name: "PARENT_CHILD", source: "Anatomy", target: "Anatomy", properties: [] },
        { name: "EXPRESSION_ABSENT", source: "Anatomy", target: "GeneOrProtein", properties: [] },
        { name: "EXPRESSION_PRESENT", source: "Anatomy", target: "GeneOrProtein", properties: [] },
        { name: "PARENT_CHILD", source: "BiologicalProcess", target: "BiologicalProcess", properties: [] },
        { name: "PARENT_CHILD", source: "Pathway", target: "Pathway", properties: [] },
        { name: "PARENT_CHILD", source: "EffectOrPhenotype", target: "EffectOrPhenotype", properties: [] },
        { name: "PARENT_CHILD", source: "CellularComponent", target: "CellularComponent", properties: [] },
        { name: "PPI", source: "GeneOrProtein", target: "GeneOrProtein", properties: [] },
        { name: "INTERACTS_WITH", source: "GeneOrProtein", target: "Pathway", properties: [] },
        { name: "INTERACTS_WITH", source: "GeneOrProtein", target: "BiologicalProcess", properties: [] },
        { name: "INTERACTS_WITH", source: "GeneOrProtein", target: "CellularComponent", properties: [] },
        { name: "INTERACTS_WITH", source: "GeneOrProtein", target: "MolecularFunction", properties: [] },
        { name: "ASSOCIATED_WITH", source: "GeneOrProtein", target: "EffectOrPhenotype", properties: [] },
        { name: "PARENT_CHILD", source: "MolecularFunction", target: "MolecularFunction", properties: [] },
        { name: "HAS", source: "Drug", target: "ApprovalStatus", properties: [] },
        { name: "TARGET", source: "Drug", target: "GeneOrProtein", properties: [] },
        { name: "IS_A", source: "Drug", target: "Category", properties: [] },
        { name: "INDICATION", source: "Drug", target: "Disease", properties: [] },
        { name: "CONTRAINDICATION", source: "Drug", target: "Disease", properties: [] },
        { name: "SYNERGISTIC_INTERACTION", source: "Drug", target: "Drug", properties: [] },
        { name: "TRANSPORTER", source: "Drug", target: "GeneOrProtein", properties: [] },
        { name: "ENZYME", source: "Drug", target: "GeneOrProtein", properties: [] },
        { name: "CARRIER", source: "Drug", target: "GeneOrProtein", properties: [] },
        { name: "SIDE_EFFECT", source: "Drug", target: "EffectOrPhenotype", properties: [] },
        { name: "OFF_LABEL_USE", source: "Drug", target: "Disease", properties: [] }
    ]
};