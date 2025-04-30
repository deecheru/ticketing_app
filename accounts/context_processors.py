def user_profile(request):
    """
    Add user profile data to all templates
    """
    if request.user.is_authenticated:
        return {
            'user_profile': request.user.profile
        }
    return {}