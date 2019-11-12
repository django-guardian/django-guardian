from .models import (
    UserObjectPermissionBase,
    UserObjectPermissionAbstract,
    GroupObjectPermissionBase,
    GroupObjectPermissionAbstract,
    Permission,
    Group
)

from guardian.utils import get_user_obj_perms_model, get_group_obj_perms_model
UserObjectPermission = get_user_obj_perms_model()
GroupObjectPermission = get_group_obj_perms_model()

