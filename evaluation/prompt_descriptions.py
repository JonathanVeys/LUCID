from pydantic import BaseModel

from evaluation.table_schema import PromptCategory


class CategoryDefinition(BaseModel):
    description:str
    pro_forma:str
    examples:list[str]

CATEGORY_DEFS: dict[PromptCategory, CategoryDefinition] = {
    PromptCategory.RETRIEVE_VALUE:CategoryDefinition(
        description="Given a set of specific cases, find attributes of those cases.",
        pro_forma="What are the values of attributes {X, Y, Z,...} in the data cases {A, B, C, ...}?",
        examples=["What is the mileage per gallon of the Audi TT?", "How long is the movie Gone with the Wind?"]
    ),
    PromptCategory.FILTER:CategoryDefinition(
        description="Given some concrete conditions on attribute values, find data cases satisfying those conditions.",
        pro_forma="Which data cases satisfy conditions {A, B, C...}?",
        examples=["What Kellogg's cereals have high fiber?", "What comedies have won awards?", "Which funds underperformed the SP-500?"]
    ),
    PromptCategory.COMPUTE_DERIVED_VALUE:CategoryDefinition(
        description="Given a set of data cases, compute an aggregate numeric representation of those data cases.",
        pro_forma="What is the value of aggregation function F over a given set S of data cases?",
        examples=["What is the average calorie content of Post cereals?", "What is the gross income of all stores combined?", "How many manufacturers of cars are there?"]
    ),
    PromptCategory.FIND_EXTREMUM:CategoryDefinition(
        description="Find data cases possessing an extreme value of an attribute over its range within the data set.",
        pro_forma="What are the top/bottom N data cases with respect to attribute A?",
        examples=["What is the car with the highest MPG?", "What director/film has won the most awards?", "What Robin Williams film has the most recent release date?"]
    ),
    PromptCategory.SORT:CategoryDefinition(
        description="Given a set of data cases, rank them according to some ordinal metric.",
        pro_forma="What is the sorted order of a set S of data cases according to their value of attribute A?",
        examples=["Order the cars by weight.", "Rank the cereals by calories."]
    ),
    PromptCategory.DETERMINE_RANGE:CategoryDefinition(
        description="Given a set of data cases and an attribute of interest, find the span of values within the set.",
        pro_forma="What is the range of values of attribute A in a set S of data cases?",
        examples=["What is the range of film lengths?", "What is the range of car horsepowers?", "What actresses are in the data set?"]
    ),
    PromptCategory.CHARACTERISE_DISTRIBUTION:CategoryDefinition(
        description="Given a set of data cases and a quantitative attribute of interest, characterize the distribution of that attribute's values over the set.",
        pro_forma="What is the distribution of values of attribute A in a set S of data cases?",
        examples=["What is the distribution of carbohydrates in cereals?", "What is the age distribution of shoppers?"]
    ),
    PromptCategory.FIND_ANOMALIES:CategoryDefinition(
        description="Identify any anomalies within a given set of data cases with respect to a given relationship or expectation, e.g. statistical outliers.",
        pro_forma="Which data cases in a set S of data cases have unexpected/exceptional values?",
        examples=["Are there exceptions to the relationship between horsepower and acceleration?", "Are there any outliers in protein?"]
    ),
    PromptCategory.CLUSTER:CategoryDefinition(
        description="Given a set of data cases, find clusters of similar attribute values.",
        pro_forma="Which data cases in a set S of data cases are similar in value for attributes {X, Y, Z, …}?",
        examples=["Are there groups of cereals w/ similar fat/calories/sugar?", "Is there a cluster of typical film lengths?"]
    ),
    PromptCategory.CORRELATE:CategoryDefinition(
        description="Given a set of data cases and two attributes, determine useful relationships between the values of those attributes.",
        pro_forma="What is the correlation between attributes X and Y over a given set S of data cases?",
        examples=["Is there a correlation between carbohydrates and fat?", "Is there a correlation between country of origin and MPG?", "Do different genders have a preferred payment method?"]
    )
}
