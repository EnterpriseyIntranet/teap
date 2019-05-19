

def edap_to_dict(obj):
    """ Transform edap object from tuple to dict """
    return {
        'fqdn': obj[0],
        'data': obj[1]
    }


def create_group_folder(nxc, group_name, group_type):
    """
    Create group folder for given group_name in group_type

    If folder for group_type doesn't exist - create folder with group_type name first and grant access to group_name,
    otherwise just give access to group_name, create subfolder in folder for group_type with group_name
    Args:
        nxc (NextCloud): nextcloud instance
        group_name (str): group name
        group_type (str): group type

    Returns (bool):
    """
    folder_id = get_group_folder(nxc, group_type)

    if folder_id is not None:
        nxc.grant_access_to_group_folder(folder_id, group_name)
    else:
        create_type_folder_res = nxc.create_group_folder(group_type)
        nxc.grant_access_to_group_folder(create_type_folder_res.data['id'], group_name)

    create_folder_res = nxc.create_group_folder("/".join([group_type, group_name]))
    grant_folder_perms_res = nxc.grant_access_to_group_folder(create_folder_res.data['id'], group_name)

    return create_folder_res.is_ok and grant_folder_perms_res.is_ok


def get_group_folder(nxc, mount_point):
    """
    Get nextcloud folder id by mount point

    Args:
        nxc: NextCloud instance
        mount_point (str): nextcloud folder mount point

    Returns:
    """
    group_folders = nxc.get_group_folders().data
    if group_folders:  # if there is no group folders, response data will be empty list
        for key, value in group_folders.items():
            if value['mount_point'] == mount_point:
                return key
    return None
