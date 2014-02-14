from Products.CMFCore.utils import getToolByName
from plone import api
from utils import expand_roles
from utils import GROUP_KEY

def has_local_roles(self):
    return self._old_has_local_roles()

def get_local_roles(self, raw=False):
    items = self._old_get_local_roles()
    if raw:
        return items
    else:
        return expand_roles(self,items)

def users_with_local_role(self, role):
    return self._old_users_with_local_role(role)

def get_local_roles_for_userid(self, userid):
    acl_users = getToolByName(self, 'acl_users')
    try:
        groups_plugin = acl_users.lr_groups
    except AttributeError:
        # the lr_groups plugin does not yet exist
        return self._old_get_local_roles_for_userid(userid)

    class dummyuser:
        def __init__(self, id):
            self.id = id
        def getId(self):
            return self.id

    groups = groups_plugin.getGroupsForPrincipal(dummyuser(userid))
    roles = self._old_get_local_roles_for_userid(userid)
    rolesdict = self.__ac_local_roles__
    for groupid in groups:
        if groupid in rolesdict:
            roles += tuple(rolesdict[groupid])
    
    return roles

def manage_addLocalRoles(self, userid, roles):
    return self._old_manage_addLocalRoles(userid, roles)

def manage_setLocalRoles(self, userid, roles):
    acl_users = getToolByName(self, 'acl_users')
    try:
        groups_plugin = acl_users.lr_groups
    except AttributeError:
        # the lr_groups plugin does not yet exist
        return self._old_manage_setLocalRoles(userid, roles)
    for role in roles:
        try:
            uuid = api.content.get_uuid(self)
        except TypeError:
            # This item doesn't have a UUID
            return self._old_manage_setLocalRoles(userid, roles)
        group_id = "%s-%s-%s" % (GROUP_KEY, uuid, role)
        try:
            groups_plugin.addGroup(group_id)
        except KeyError:
            pass  # group already exists

        # work out if we have to remove from any groups
        current_roles = self._old_get_local_roles()
        for groupid,roles2 in current_roles:
            if groupid.startswith(GROUP_KEY):
                for id,login in groups_plugin.listAssignedPrincipals(groupid):
                    if id == userid and roles2[0] not in roles:
                        groups_plugin.removePrincipalFromGroup(userid, groupid)
                        break

        groups_plugin.manage_addPrincipalsToGroup(group_id, [userid])
        if role not in self.get_local_roles_for_userid(group_id):
            self._old_manage_setLocalRoles(group_id, [role])


def manage_delLocalRoles(self, userids):
    """Remove all local roles for a user."""
    acl_users = getToolByName(self, 'acl_users')
    groups_plugin = acl_users.lr_groups

    rolesdict = self.__ac_local_roles__
    roles = rolesdict.keys()
    for userid in userids:
        for groupid in roles:
            if groupid.startswith(GROUP_KEY):
                groups_plugin.removePrincipalFromGroup(userid, groupid)


    return self._old_manage_delLocalRoles(userids)
