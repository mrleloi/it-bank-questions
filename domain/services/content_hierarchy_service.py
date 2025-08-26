class ContentHierarchyService:
    def __init__(self, repository):
        self.repository = repository

    def get_hierarchy(self, content_id):
        return self.repository.fetch_hierarchy(content_id)

    def add_content(self, parent_id, content_data):
        return self.repository.insert_content(parent_id, content_data)

    def remove_content(self, content_id):
        return self.repository.delete_content(content_id)
