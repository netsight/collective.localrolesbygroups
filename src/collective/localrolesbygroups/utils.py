from Products.CMFCore.utils import getToolByName
GROUP_KEY = 'lrgroup'

def expand_roles(self, items):
    try:
        acl_users = getToolByName(self, 'acl_users')
        groups_plugin = acl_users.lr_groups
    except AttributeError:
        # lr_groups doesn't exist yet
        return items
    res = {}
    for userid,roles in items:
        if userid.startswith(GROUP_KEY):
            for exp_userid, exp_username in groups_plugin.listAssignedPrincipals(userid):
                res[exp_userid] = res.get(exp_userid, ()) + tuple(roles)
        else:
            res[userid] = res.get(userid, ()) + tuple(roles)

    keys = res.keys()
    keys.sort()
    return tuple([ (key, tuple(res[key])) for key in keys])
