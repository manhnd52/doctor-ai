from enum import Enum

class CypherError(Enum):
    def __new__(cls, value, description):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.description = description
        return obj

    LIMIT_UNNESSARY = (
        "LIMIT_UNNESSARY",
        "The question does not require a limit clause, but it is present in the query."
    )
    DIRTY_NULL = (
        "DIRTY_NULL",
        "The query contains a NULL value that is not properly handled, which may lead to unexpected results."
    )
    OTHER = (
        "OTHER",
        "Any other common error that does not fall into the above categories."
    )

if __name__ == "__main__":
    for error in CypherError:
        print(f"{error.name}: {error.description}")