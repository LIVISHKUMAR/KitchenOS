"""GraphQL endpoint."""

from fastapi import APIRouter

router = APIRouter()

try:
    from strawberry.fastapi import GraphQLRouter
    from app.api.graphql.schema import schema
    graphql_app = GraphQLRouter(schema)
    router.include_router(graphql_app, prefix="/graphql")
except ImportError:
    # Strawberry not installed, skip GraphQL
    pass
