from Products.CMFCore.utils import getToolByName

from plone.memoize.instance import memoize
from plone.memoize.instance import clearafter

from plone.app.workflow.browser.sharing import SharingView as BaseView
from plone.app.workflow import PloneMessageFactory as _

from plone import api

from collective.localrolesbygroups.utils import GROUP_KEY

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

        before = self.context.get_local_roles(raw=True)
        changed = BaseView.update_role_settings(self, new_settings, reindex=False)
        after = self.context.get_local_roles(raw=True)
        if reindex and dict(before) != dict(after):
            self.context.reindexObjectSecurity()
        return changed

            

