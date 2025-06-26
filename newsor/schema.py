import graphene
import graphql_jwt
from django.contrib.auth import authenticate
from api.schema import Query as ApiQuery, Mutation as ApiMutation, UserType


class ObtainJSONWebTokenWithUser(graphene.Mutation):
    """
    Custom JWT token mutation that returns both token and user data
    """
    token = graphene.String()
    refresh_token = graphene.String()
    user = graphene.Field(UserType)
    
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
    
    @classmethod
    def mutate(cls, root, info, username, password):
        user = authenticate(username=username, password=password)
        
        if not user:
            raise Exception('Please enter valid credentials')
        
        if not user.is_active:
            raise Exception('User account is disabled')
        
        # Use the built-in JWT token generation
        from graphql_jwt.shortcuts import get_token
        
        token = get_token(user)
        
        # Generate refresh token if enabled
        refresh_token = None
        try:
            from graphql_jwt.refresh_token.shortcuts import create_refresh_token
            refresh_token = create_refresh_token(user)
        except Exception:
            pass
        
        return cls(
            token=token,
            refresh_token=refresh_token,
            user=user
        )


class Query(ApiQuery, graphene.ObjectType):
    """
    Root GraphQL Query
    """
    pass


class Mutation(ApiMutation, graphene.ObjectType):
    """
    Root GraphQL Mutation
    """
    token_auth = ObtainJSONWebTokenWithUser.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
