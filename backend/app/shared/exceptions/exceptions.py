from fastapi import HTTPException


class NotFoundException(HTTPException):

    def __init__(self, detail="Registro no encontrado"):

        super().__init__(
            status_code=404,
            detail=detail,
        )


class BadRequestException(HTTPException):

    def __init__(self, detail):

        super().__init__(
            status_code=400,
            detail=detail,
        )


class UnauthorizedException(HTTPException):

    def __init__(self):

        super().__init__(
            status_code=401,
            detail="No autorizado",
        )