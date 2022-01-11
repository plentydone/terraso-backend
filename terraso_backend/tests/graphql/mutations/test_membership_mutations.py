import pytest

from apps.core.models import Membership

pytestmark = pytest.mark.django_db


def test_membership_add(client_query, groups, users):
    group = groups[0]
    user = users[0]

    response = client_query(
        """
        mutation addMembership($input: MembershipAddMutationInput!){
          addMembership(input: $input) {
            membership {
              id
              userRole
              user {
                email
              }
              group {
                slug
              }
            }
          }
        }
        """,
        variables={
            "input": {
                "userEmail": user.email,
                "groupSlug": group.slug,
            }
        },
    )
    membership = response.json()["data"]["addMembership"]["membership"]

    assert membership["id"]
    assert membership["user"]["email"] == user.email
    assert membership["group"]["slug"] == group.slug
    assert membership["userRole"] == Membership.ROLE_MEMBER.upper()


def test_membership_add_duplicated(client_query, memberships):
    group = memberships[0].group
    user = memberships[0].user

    response = client_query(
        """
        mutation addMembership($input: MembershipAddMutationInput!){
          addMembership(input: $input) {
            membership {
              id
              userRole
              user {
                email
              }
              group {
                slug
              }
            }
          }
        }
        """,
        variables={
            "input": {
                "userEmail": user.email,
                "groupSlug": group.slug,
            }
        },
    )
    error_result = response.json()["errors"][0]

    assert "Group and User already exists" in error_result["message"]


def test_membership_add_manager(client_query, groups, users):
    group = groups[0]
    user = users[0]

    response = client_query(
        """
        mutation addMembership($input: MembershipAddMutationInput!){
          addMembership(input: $input) {
            membership {
              id
              userRole
              user {
                email
              }
              group {
                slug
              }
            }
          }
        }
        """,
        variables={
            "input": {
                "userEmail": user.email,
                "groupSlug": group.slug,
                "userRole": Membership.ROLE_MANAGER,
            }
        },
    )
    membership = response.json()["data"]["addMembership"]["membership"]

    assert membership["id"]
    assert membership["user"]["email"] == user.email
    assert membership["group"]["slug"] == group.slug
    assert membership["userRole"] == Membership.ROLE_MANAGER.upper()


def test_membership_update(client_query, memberships):
    old_membership = memberships[0]

    assert old_membership.user_role != Membership.ROLE_MANAGER.upper()

    response = client_query(
        """
        mutation updateMembership($input: MembershipUpdateMutationInput!){
          updateMembership(input: $input) {
            membership {
              id
              userRole
              user {
                email
              }
              group {
                slug
              }
            }
          }
        }
        """,
        variables={
            "input": {
                "id": str(old_membership.id),
                "userRole": Membership.ROLE_MANAGER,
            }
        },
    )
    membership = response.json()["data"]["updateMembership"]["membership"]

    assert membership["id"]
    assert membership["user"]["email"] == old_membership.user.email
    assert membership["group"]["slug"] == old_membership.group.slug
    assert membership["userRole"] == Membership.ROLE_MANAGER.upper()


def test_membership_delete(client_query, memberships):
    old_membership = memberships[0]

    client_query(
        """
        mutation deleteMembership($input: MembershipDeleteMutationInput!){
          deleteMembership(input: $input) {
            membership {
              user {
                email
              },
              group {
                slug
              }
            }
          }
        }
        """,
        variables={
            "input": {
                "id": str(old_membership.id),
            }
        },
    )

    assert not Membership.objects.filter(user=old_membership.user, group=old_membership.group)