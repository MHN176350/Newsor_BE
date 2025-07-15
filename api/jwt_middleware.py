"""
Custom GraphQL JWT middleware that skips authentication for specific mutations
"""
from graphql_jwt.middleware import JSONWebTokenMiddleware
from graphql import GraphQLError


class SelectiveJWTMiddleware(JSONWebTokenMiddleware):
    """
    JWT middleware that skips authentication for specific mutations
    """
    
    # List of mutations that don't require authentication
    PUBLIC_MUTATIONS = [
        'requestPasswordReset',
        'resetPassword',
       
    ]
    
    def resolve(self, next, root, info, **args):
        """
        Override resolve to skip JWT validation for public mutations
        """
        # Get the operation name/mutation name
        operation_name = None
        if hasattr(info, 'operation') and info.operation:
            if hasattr(info.operation, 'selection_set') and info.operation.selection_set:
                selections = info.operation.selection_set.selections
                if selections:
                    operation_name = selections[0].name.value
        
        # Skip JWT validation for public mutations
        if operation_name in self.PUBLIC_MUTATIONS:
            return next(root, info, **args)
        
        # Apply normal JWT validation for all other operations
        return super().resolve(next, root, info, **args)
