# Generated by Django 4.2.5 on 2023-09-15 15:27

from django.db import migrations

from apps.project_management import collaboration_roles


def migrate_forward(apps, schema_editor):
    Project = apps.get_model("project_management", "Project")
    MembershipList = apps.get_model("collaboration", "MembershipList")
    Membership = apps.get_model("collaboration", "Membership")
    # The example docs https://docs.djangoproject.com/en/4.2/ref/migration-operations/#runpython
    # use the db_alias.
    # probably not technically necessary because we don't use multiple DBs
    db_alias = schema_editor.connection.alias
    for project in Project.objects.using(db_alias).all():
        group = project.group
        project.membership_list = MembershipList.objects.using(db_alias).create(
            membership_type="open",
            enroll_method="join",
        )
        # add group memberships to membership list
        for membership in group.memberships.all():
            user_role = (
                collaboration_roles.ROLE_MANAGER
                if membership.user_role == "manager"
                else collaboration_roles.ROLE_VIEWER
            )

            if (
                Membership.objects.using(db_alias)
                .filter(user=membership.user, membership_list=project.membership_list)
                .exists()
            ):
                # it seems like group constraints are not as strict as MembershipLists
                # if there are several Memberships with the same user, just ignore
                # (this was happening with my local DB instance)
                continue
            Membership.objects.using(db_alias).create(
                user=membership.user,
                membership_list=project.membership_list,
                user_role=user_role,
                membership_status="approved",
            )
            # clean up
            membership.delete()
        project.group.delete()
        project.group = None
        project.save()


class Migration(migrations.Migration):
    dependencies = [
        ("project_management", "0015_remove_project_group_project_membership_list"),
    ]

    operations = [migrations.RunPython(migrate_forward, atomic=True)]
