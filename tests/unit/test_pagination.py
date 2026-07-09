from app.utils.pagination import paginate


def test_paginate_basic():
    items = [1,2, 3]
    result = paginate(items=items, total=10, page=1, per_page=3)
    assert result.items == [1, 2, 3]
    assert result.total == 10
    assert result.page == 1
    assert result.per_page == 3
    assert result.pages ==  4
    
    
def test_paginate_single_page():
    result = paginate([], total=5, page=1, per_page=20)
    assert result.pages == 1
    
    
def test_paginate_empty():
    result = paginate([], total=0, page=1, per_page=20)
    assert result.pages == 0
    assert result.total == 0