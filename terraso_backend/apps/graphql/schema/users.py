import graphene
import graphql_relay
from graphene import relay
from graphene_django import DjangoObjectType

from apps.core.models import User

from .commons import BaseDeleteMutation


class UserNode(DjangoObjectType):
    class Meta:
        model = User
        filter_fields = {
            "email": ["icontains"],
            "first_name": ["icontains"],
            "last_name": ["icontains"],
        }
        interfaces = (relay.Node,)


class UserAddMutation(relay.ClientIDMutation):
    user = graphene.Field(UserNode)

    class Input:
        first_name = graphene.String()
        last_name = graphene.String()
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        user = User.objects.create_user(
            kwargs.pop("email"), password=kwargs.pop("password"), **kwargs
        )

        return cls(user=user)


class UserUpdateMutation(relay.ClientIDMutation):
    user = graphene.Field(UserNode)

    model_class = User

    class Input:
        id = graphene.ID(required=True)
        first_name = graphene.String()
        last_name = graphene.String()
        email = graphene.String()
        password = graphene.String()

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        graphql_id = kwargs.pop("id")

        _, _pk = graphql_relay.from_global_id(graphql_id)
        user = User.objects.get(pk=_pk)
        new_password = kwargs.pop("password", None)

        if new_password:
            user.set_password(new_password)

        for attr, value in kwargs.items():
            setattr(user, attr, value)

        user.save()

        return cls(user=user)


class UserDeleteMutation(BaseDeleteMutation):
    user = graphene.Field(UserNode)
    model_class = User

    class Input:
        id = graphene.ID()
