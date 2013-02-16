from mock import Mock
from mock import patch
from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group, AnonymousUser

from guardian.compat import get_user_model
from guardian.tests.core_test import ObjectPermissionTestCase
from guardian.tests.testapp.models import Project
from guardian.tests.testapp.models import ProjectUserObjectPermission
from guardian.tests.testapp.models import ProjectGroupObjectPermission
from guardian.models import UserObjectPermission
from guardian.models import GroupObjectPermission
from guardian.utils import get_anonymous_user
from guardian.utils import get_identity
from guardian.utils import get_user_obj_perms_model
from guardian.utils import get_group_obj_perms_model
from guardian.exceptions import NotUserNorGroup
from guardian.models import Group, AnonymousUser

User = get_user_model()

class GetAnonymousUserTest(TestCase):

    def test(self):
        anon = get_anonymous_user()
        self.assertTrue(isinstance(anon, User))

class GetIdentityTest(ObjectPermissionTestCase):

    def test_user(self):
        user, group = get_identity(self.user)
        self.assertTrue(isinstance(user, User))
        self.assertEqual(group, None)

    def test_anonymous_user(self):
        anon = AnonymousUser()
        user, group = get_identity(anon)
        self.assertTrue(isinstance(user, User))
        self.assertEqual(group, None)

    def test_group(self):
        user, group = get_identity(self.group)
        self.assertTrue(isinstance(group, Group))
        self.assertEqual(user, None)

    def test_not_user_nor_group(self):
        self.assertRaises(NotUserNorGroup, get_identity, 1)
        self.assertRaises(NotUserNorGroup, get_identity, "User")
        self.assertRaises(NotUserNorGroup, get_identity, User)


class GetUserObjPermsModelTest(TestCase):

    def test_for_instance(self):
        project = Project(name='Foobar')
        self.assertEqual(get_user_obj_perms_model(project),
            ProjectUserObjectPermission)

    def test_for_class(self):
        self.assertEqual(get_user_obj_perms_model(Project),
            ProjectUserObjectPermission)

    def test_default(self):
        self.assertEqual(get_user_obj_perms_model(ContentType),
            UserObjectPermission)

    def test_user_model(self):
        # this test assumes that there were no direct obj perms model to User
        # model defined (i.e. while testing guardian app in some custom project)
        self.assertEqual(get_user_obj_perms_model(User),
            UserObjectPermission)


class GetGroupObjPermsModelTest(TestCase):

    def test_for_instance(self):
        project = Project(name='Foobar')
        self.assertEqual(get_group_obj_perms_model(project),
            ProjectGroupObjectPermission)

    def test_for_class(self):
        self.assertEqual(get_group_obj_perms_model(Project),
            ProjectGroupObjectPermission)

    def test_default(self):
        self.assertEqual(get_group_obj_perms_model(ContentType),
            GroupObjectPermission)

    def test_group_model(self):
        # this test assumes that there were no direct obj perms model to Group
        # model defined (i.e. while testing guardian app in some custom project)
        self.assertEqual(get_group_obj_perms_model(Group),
            GroupObjectPermission)

