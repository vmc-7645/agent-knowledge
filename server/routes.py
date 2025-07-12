@router.post("/add-question")
def add_question(content: str):
    # embed -> store in DB -> return ID
    pass

@router.post("/search-question")
def search_question(content: str):
    # embed -> search DB -> return IDs
    pass

@router.post("/add-context")
def add_context(content: str):
    # embed -> store in DB -> return ID
    pass

@router.post("/search-context")
def search_context(content: str):
    # embed -> search DB -> return IDs
    pass
