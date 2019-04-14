

def edap_to_dict(obj):
    """ Transform edap object from tuple to dict """
    return {
        'fqdn': obj[0],
        'data': obj[1]
    }
