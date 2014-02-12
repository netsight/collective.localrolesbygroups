from itertools import chain

from plone.memoize.instance import memoize, clearafter
from zope.component import getUtilitiesFor, getMultiAdapter
from zope.i18n import translate

from Acquisition import aq_parent, aq_base
from AccessControl import Unauthorized
from zExceptions import Forbidden

from Products.CMFCore.utils import getToolByName
from Products.CMFCore import permissions
from Products.CMFPlone.utils import normalizeString, safe_unicode
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage

from plone.app.workflow import PloneMessageFactory as _
from plone.app.workflow.interfaces import ISharingPageRole

import json

from plone.api.content import get_uuid

from plone.app.workflow.browser.sharing import SharingView as BaseView

AUTH_GROUP = 'AuthenticatedUsers'
STICKY = (AUTH_GROUP, )

class SharingView(BaseView):

    @clearafter
    def update_role_settings(self, new_settings, reindex=True):
        """Update local role settings and reindex object security if necessary.

        new_settings is a list of dicts with keys id, for the user/group id;
        type, being either 'user' or 'group'; and roles, containing the list
        of role ids that are set.

        Returns True if changes were made, or False if the new settings
        are the same as the existing settings.
        """

        changed = False
        context = self.context

        managed_roles = frozenset([r['id'] for r in self.roles()])
        member_ids_to_clear = []

        for s in new_settings:
            user_id = s['id']

            existing_roles = frozenset(context.get_local_roles_for_userid(userid=user_id))
            selected_roles = frozenset(s['roles'])

            relevant_existing_roles = managed_roles & existing_roles

            # If, for the managed roles, the new set is the same as the
            # current set we do not need to do anything.
            if relevant_existing_roles == selected_roles:
                continue

            # We will remove those roles that we are managing and which set
            # on the context, but which were not selected
            to_remove = relevant_existing_roles - selected_roles

            # Leaving us with the selected roles, less any roles that we
            # want to remove
            wanted_roles = (selected_roles | existing_roles) - to_remove

            # take away roles that we are managing, that were not selected
            # and which were part of the existing roles

            if wanted_roles:
                # xxx maybe use groups tool?
                acl_users = getToolByName(context, 'acl_users')
                groups_plugin = acl_users.lr_groups
                for role in list(wanted_roles):
                    group_id = "lrgroup-%s-%s" % (get_uuid(context), role)
                    try:
                        groups_plugin.addGroup(group_id)
                    except KeyError:
                        pass # group already exists
                    groups_plugin.manage_addPrincipalsToGroup(group_id, [user_id])
                    if role not in context.get_local_roles_for_userid(group_id):
                        context.manage_setLocalRoles(group_id, [role])
                

#                context.manage_setLocalRoles(user_id, list(wanted_roles))
                changed = True
            elif existing_roles:
                member_ids_to_clear.append(user_id)

        if member_ids_to_clear:
            context.manage_delLocalRoles(userids=member_ids_to_clear)
            changed = True

        if changed and reindex:
            self.context.reindexObjectSecurity()

        return changed

    @memoize
    def existing_role_settings(self):
        """Get current settings for users and groups that have already got
        at least one of the managed local roles.

        Returns a list of dicts as per role_settings()
        """
        context = self.context

        portal_membership = getToolByName(context, 'portal_membership')
        portal_groups = getToolByName(context, 'portal_groups')
        acl_users = getToolByName(context, 'acl_users')

        info = []

        # This logic is adapted from computeRoleMap.py

        local_roles = acl_users._getLocalRolesForDisplay(context)
        acquired_roles = self._inherited_roles() + self._borg_localroles()
        available_roles = [r['id'] for r in self.roles()]


        # first process acquired roles
        items = {}
        for name, roles, rtype, rid in expand_roles(context, acquired_roles):
            items[rid] = dict(id = rid,
                              name = name,
                              type = rtype,
                              sitewide = [],
                              acquired = roles,
                              local = [], )

        # second process local roles
        for name, roles, rtype, rid in expand_roles(context, local_roles):
            if rid in items:
                items[rid]['local'] = roles
            else:
                items[rid] = dict(id = rid,
                                  name = name,
                                  type = rtype,
                                  sitewide = [],
                                  acquired = [],
                                  local = roles, )

        # Make sure we always get the authenticated users virtual group
        if AUTH_GROUP not in items:
            items[AUTH_GROUP] = dict(id = AUTH_GROUP,
                                     name = _(u'Logged-in users'),
                                     type = 'group',
                                     sitewide = [],
                                     acquired = [],
                                     local = [], )

        # If the current user has been given roles, remove them so that he
        # doesn't accidentally lock himself out.

        member = portal_membership.getAuthenticatedMember()
        if member.getId() in items:
            items[member.getId()]['disabled'] = True

        # Sort the list: first the authenticated users virtual group, then
        # all other groups and then all users, alphabetically

        dec_users = [(a['id'] not in self.STICKY,
                       a['type'],
                       a['name'],
                       a) for a in items.values()]
        dec_users.sort()

        # Add the items to the info dict, assigning full name if possible.
        # Also, recut roles in the format specified in the docstring

        for d in dec_users:
            item = d[-1]
            name = item['name']
            rid = item['id']
            global_roles = set()

            if item['type'] == 'user':
                member = acl_users.getUserById(rid)
                if member is not None:
                    name = member.getProperty('fullname') or member.getId() or name
                    global_roles = set(member.getRoles())
            elif item['type'] == 'group':
                g = portal_groups.getGroupById(rid)
                name = g.getGroupTitleOrName()
                global_roles = set(g.getRoles())

                # This isn't a proper group, so it needs special treatment :(
                if rid == AUTH_GROUP:
                    name = _(u'Logged-in users')

            info_item = dict(id = item['id'],
                             type = item['type'],
                             title = name,
                             disabled = item.get('disabled', False),
                             roles = {})

            # Record role settings
            have_roles = False
            for r in available_roles:
                if r in global_roles:
                    info_item['roles'][r] = 'global'
                elif r in item['acquired']:
                    info_item['roles'][r] = 'acquired'
                    have_roles = True # we want to show acquired roles
                elif r in item['local']:
                    info_item['roles'][r] = True
                    have_roles = True # at least one role is set
                else:
                    info_item['roles'][r] = False

            if have_roles or rid in self.STICKY:
                info.append(info_item)

        return info

def expand_roles(context, userroles):
    # expand out the groups roles
    expanded_userroles = []
    acl_users = getToolByName(context, 'acl_users')
    for user, roles, role_type, name in userroles:
        if user.startswith('lrgroup-') and role_type == 'group':
            for exp_userid,exp_username in acl_users.lr_groups.listAssignedPrincipals(user):
                expanded_userroles.append((exp_userid, roles, 'user', exp_username))
        else:
            expanded_userroles.append((user, roles, role_type, name))
                        
    return expanded_userroles


