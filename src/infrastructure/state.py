from data.owners import Owner


active_account: Owner = None


def reload_account():
    global active_account
    if not active_account:
        return

    active_account = Owner.objects().filter(id=active_account.id).first()
    pass
