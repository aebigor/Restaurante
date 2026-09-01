class BaseService:

    def __init__(self, repository):

        self.repository = repository

    def get_all(self):

        return self.repository.get_all()

    def get_by_id(self, id):

        return self.repository.get_by_id(id)

    def create(self, obj):

        return self.repository.create(obj)

    def update(self):

        return self.repository.update()

    def delete(self, obj):

        return self.repository.delete(obj)