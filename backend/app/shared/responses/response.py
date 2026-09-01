def success(data=None, message="OK"):

    return {
        "success": True,
        "message": message,
        "data": data,
    }


def error(message):

    return {
        "success": False,
        "message": message,
    }