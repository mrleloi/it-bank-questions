class GetUserProfileUseCase:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    def execute(self, user_id):
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "profile_picture": user.profile_picture,
        }


class UpdateUserProfileUseCase:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    def execute(self, user_id, update_data):
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        for key, value in update_data.items():
            setattr(user, key, value)
        self.user_repository.save(user)
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "profile_picture": user.profile_picture,
        }


class UpdateUserSettingsUseCase:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    def execute(self, user_id, settings):
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        user.settings.update(settings)
        self.user_repository.save(user)
        return {"status": "Settings updated"}


class DeleteUserAccountUseCase:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    def execute(self, user_id):
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        self.user_repository.delete(user)
        return {"status": "Account deleted"}
