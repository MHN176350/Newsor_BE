"""
Updated GraphQL schema using Clean Architecture approach.
"""

import graphene
from .core.interfaces.graphql.news_schema import NewsQuery, NewsMutation
from api.schema import (
    # Keep existing types and queries that aren't refactored yet
    UserType, CategoryType, TagType, UserProfileType, CommentType,
    Query as ExistingQuery, Mutation as ExistingMutation
)


class Query(NewsQuery, ExistingQuery, graphene.ObjectType):
    """Combined GraphQL queries."""
    pass


class Mutation(NewsMutation, ExistingMutation, graphene.ObjectType):
    """Combined GraphQL mutations."""
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
