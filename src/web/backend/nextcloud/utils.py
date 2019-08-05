import logging

from flask import g, current_app

from nextcloud import NextCloud
from nextcloud.base import Permission

logger = logging.getLogger()


def get_nextcloud():
    """ Create if doesn't exist or return edap from flask g object """
    if 'nextcloud' not in g:
        g.nextcloud = NextCloud(endpoint=current_app.config['NEXTCLOUD_HOST'],
                                user=current_app.config['NEXTCLOUD_USER'],
                                password=current_app.config['NEXTCLOUD_PASSWORD'])
    return g.nextcloud


def create_group_folder(group_name, group_type):
    """
    Create group folder for given group_name in group_type

    If folder for group_type doesn't exist - create folder with group_type name first and grant access to group_name,
    otherwise just give access to group_name, create subfolder in folder for group_type with group_name
    Args:
        group_name (str): group name
        group_type (str): group type

    Returns (bool):
    """
    nxc = get_nextcloud()
    folder_id = get_group_folder(group_type)
    # FIXME: access granted to wrong group (on franchise folder example)
    # issue that nextcloud reads some franchises by Description, not CN
    if folder_id is not None:
        nxc.grant_access_to_group_folder(folder_id, group_name)
    else:
        create_type_folder_res = nxc.create_group_folder(group_type)
        nxc.grant_access_to_group_folder(create_type_folder_res.data['id'], group_name)

    create_folder_res = nxc.create_group_folder("/".join([group_type, group_name]))
    grant_folder_perms_res = nxc.grant_access_to_group_folder(create_folder_res.data['id'], group_name)

    return create_folder_res.is_ok and grant_folder_perms_res.is_ok


def get_group_folder(mount_point):
    """
    Get nextcloud folder id by mount point

    Args:
        mount_point (str): nextcloud folder mount point

    Returns:
    """
    nxc = get_nextcloud()
    group_folders = nxc.get_group_folders().data
    if group_folders:  # if there is no group folders, response data will be empty list
        for key, value in group_folders.items():
            if value['mount_point'] == mount_point:
                return key
    return None


def check_consistency():
    """ Check if all required system objects exist in Edap """
    from backend.ldap.models import Franchise, Division
    nxc = get_nextcloud()

    main_franchises_folder_id = get_group_folder(Franchise.GROUP_FOLDER)
    if not main_franchises_folder_id:
        logger.warning('Nextcloud main franchises folder is missing. '
                       'It will be created automatically, when new franchise is created')

    # check permission for everybody team
    if main_franchises_folder_id:
        main_franchises_folder = nxc.get_group_folder(main_franchises_folder_id).data
        if 'everybody' not in main_franchises_folder['groups']:
            logger.warning('Nextcloud main franchises folder doesn\'t have Read permission for Everybody Team')
        elif main_franchises_folder['groups']['everybody'] != Permission.READ:
            logger.warning('Nextcloud main franchises folder has wrong permissions for Everybody Team')

    main_divisions_folder = get_group_folder(Division.GROUP_FOLDER)
    if not main_divisions_folder:
        logger.warning('Nextcloud main divisions folder is missing. '
                       'It will be created automatically, when new division is created')
