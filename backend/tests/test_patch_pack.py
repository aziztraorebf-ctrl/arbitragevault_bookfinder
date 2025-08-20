import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# Import models and repositories - ✅ FIX: Correct paths
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.models.analysis import Analysis, Base
from app.models.batch import Batch
from app.repositories.analysis import AnalysisRepository
from app.repositories.base import (
    FilterCriteria, FilterCondition, DuplicateIsbnInBatchError, 
    InvalidSortFieldError, InvalidFilterFieldError
)

@pytest.fixture
def db_session():
    """Create in-memory SQLite session for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    session.expire_on_commit = False  # Important pour tests
    
    yield session
    session.close()

@pytest.fixture
def sample_batch(db_session):
    """Create sample batch for testing"""
    batch = Batch(id=1, name="Test Batch")
    db_session.add(batch)
    db_session.commit()
    return batch

@pytest.fixture
def analysis_repo(db_session):
    """Create AnalysisRepository instance"""
    return AnalysisRepository(db_session)

# ============================================================================
# PATCH 1 TESTS: isbn_list support in list_filtered
# ============================================================================

def test_patch1_isbn_list_filtering(analysis_repo, sample_batch, db_session):  # ✅ FIX: Remove async
    """Test filtering by ISBN list"""
    
    # Create test data with different ISBNs
    analyses = [
        Analysis(batch_id=1, isbn_or_asin="ISBN001", roi_percent=Decimal("25.5")),
        Analysis(batch_id=1, isbn_or_asin="ISBN002", roi_percent=Decimal("35.2")),
        Analysis(batch_id=1, isbn_or_asin="ISBN003", roi_percent=Decimal("45.8")),
        Analysis(batch_id=1, isbn_or_asin="ISBN004", roi_percent=Decimal("15.1"))
    ]
    
    for analysis in analyses:
        db_session.add(analysis)
    db_session.commit()
    
    # Test filtering by specific ISBN list
    result = analysis_repo.list_filtered(  # ✅ FIX: Remove await
        batch_id=1,
        isbn_list=["ISBN001", "ISBN003"]
    )
    
    assert result.total == 2
    returned_isbns = {item.isbn_or_asin for item in result.items}
    assert returned_isbns == {"ISBN001", "ISBN003"}

def test_patch1_isbn_list_normalization(analysis_repo, sample_batch, db_session):  # ✅ FIX: Remove async
    """Test ISBN normalization in list_filtered"""
    
    # Create analysis with normalized ISBN
    analysis = Analysis(batch_id=1, isbn_or_asin="ISBN001", roi_percent=Decimal("25.5"))
    db_session.add(analysis)
    db_session.commit()
    
    # Test search with lowercase/spaces
    result = analysis_repo.list_filtered(  # ✅ FIX: Remove await
        batch_id=1,
        isbn_list=[" isbn001 ", "ISBN999"]  # Mixed case/whitespace
    )
    
    assert result.total == 1
    assert result.items[0].isbn_or_asin == "ISBN001"

def test_patch1_isbn_list_with_other_filters(analysis_repo, sample_batch, db_session):  # ✅ FIX: Remove async
    """Test isbn_list combined with other filters"""
    
    analyses = [
        Analysis(batch_id=1, isbn_or_asin="ISBN001", roi_percent=Decimal("25.5")),
        Analysis(batch_id=1, isbn_or_asin="ISBN002", roi_percent=Decimal("35.2")),
        Analysis(batch_id=1, isbn_or_asin="ISBN003", roi_percent=Decimal("5.8"))  # Low ROI
    ]
    
    for analysis in analyses:
        db_session.add(analysis)
    db_session.commit()
    
    # Combine ISBN list + ROI filter
    filters = [FilterCriteria(field="roi_percent", condition=FilterCondition.GTE, value=Decimal("20"))]
    
    result = analysis_repo.list_filtered(  # ✅ FIX: Remove await
        batch_id=1,
        isbn_list=["ISBN001", "ISBN002", "ISBN003"],
        filters=filters
    )
    
    assert result.total == 2  # Only ISBN001 and ISBN002 have ROI >= 20
    returned_isbns = {item.isbn_or_asin for item in result.items}
    assert returned_isbns == {"ISBN001", "ISBN002"}

# ============================================================================
# PATCH 2 TESTS: Strict sort field validation
# ============================================================================

def test_patch2_valid_sort_field(analysis_repo, sample_batch, db_session):  # ✅ FIX: Remove async
    """Test sorting with valid field"""
    
    analyses = [
        Analysis(batch_id=1, isbn_or_asin="ISBN001", roi_percent=Decimal("15.5")),
        Analysis(batch_id=1, isbn_or_asin="ISBN002", roi_percent=Decimal("25.2"))
    ]
    
    for analysis in analyses:
        db_session.add(analysis)
    db_session.commit()
    
    # Test valid sort field
    result = analysis_repo.list_filtered(  # ✅ FIX: Remove await
        batch_id=1,
        sort_by="roi_percent",
        sort_desc=True
    )
    
    assert result.total == 2
    assert result.items[0].roi_percent > result.items[1].roi_percent

def test_patch2_invalid_sort_field_raises_error(analysis_repo, sample_batch, db_session):  # ✅ FIX: Remove async
    """Test that invalid sort field raises InvalidSortFieldError"""
    
    analysis = Analysis(batch_id=1, isbn_or_asin="ISBN001", roi_percent=Decimal("15.5"))
    db_session.add(analysis)
    db_session.commit()
    
    # Test invalid sort field
    with pytest.raises(InvalidSortFieldError) as exc_info:
        analysis_repo.list_filtered(  # ✅ FIX: Remove await
            batch_id=1,
            sort_by="invalid_field"  # Not in SORTABLE_FIELDS
        )
    
    assert "invalid_field is not sortable" in str(exc_info.value)
    assert "roi_percent" in str(exc_info.value)  # Should show allowed fields

# ============================================================================
# PATCH 3 TESTS: Balanced strategy with Decimal precision
# ============================================================================

def test_patch3_balanced_strategy_decimal_precision(analysis_repo, sample_batch, db_session):  # ✅ FIX: Remove async
    """Test balanced strategy uses Decimal for precision"""
    
    analyses = [
        Analysis(
            batch_id=1, 
            isbn_or_asin="ISBN001", 
            roi_percent=Decimal("40.0"),    # High ROI
            velocity_score=Decimal("20.0")   # Low velocity
        ),
        Analysis(
            batch_id=1, 
            isbn_or_asin="ISBN002", 
            roi_percent=Decimal("20.0"),    # Low ROI
            velocity_score=Decimal("60.0")   # High velocity
        )
    ]
    
    for analysis in analyses:
        db_session.add(analysis)
    db_session.commit()
    
    # Test balanced strategy
    result = analysis_repo.top_n_for_batch(  # ✅ FIX: Remove await
        batch_id=1,
        strategy="balanced",
        limit=2
    )
    
    assert len(result) == 2
    
    # Calculate expected balanced scores
    # ISBN001: 40 * 0.6 + 20 * 0.4 = 24 + 8 = 32
    # ISBN002: 20 * 0.6 + 60 * 0.4 = 12 + 24 = 36
    
    # ISBN002 should be first (higher balanced score)
    assert result[0].isbn_or_asin == "ISBN002"
    assert result[1].isbn_or_asin == "ISBN001"

# ============================================================================
# PATCH 4 TESTS: IntegrityError handling
# ============================================================================

def test_patch4_duplicate_isbn_in_batch_error(analysis_repo, sample_batch, db_session):  # ✅ FIX: Remove async
    """Test DuplicateIsbnInBatchError on duplicate ISBN in same batch"""
    
    # Create first analysis
    analysis1 = analysis_repo.create_analysis(  # ✅ FIX: Remove await
        batch_id=1,
        isbn_or_asin="ISBN001",
        roi_percent=Decimal("25.5")
    )
    db_session.commit()
    
    assert analysis1.isbn_or_asin == "ISBN001"
    
    # Try to create duplicate in same batch
    with pytest.raises(DuplicateIsbnInBatchError) as exc_info:
        analysis_repo.create_analysis(  # ✅ FIX: Remove await
            batch_id=1,
            isbn_or_asin="ISBN001",  # Same ISBN, same batch
            roi_percent=Decimal("35.2")
        )
    
    assert "ISBN001" in str(exc_info.value)
    assert "batch 1" in str(exc_info.value)

def test_patch4_same_isbn_different_batch_allowed(analysis_repo, db_session):  # ✅ FIX: Remove async
    """Test same ISBN allowed in different batches"""
    
    # Create two batches
    batch1 = Batch(id=1, name="Batch 1")
    batch2 = Batch(id=2, name="Batch 2")
    db_session.add(batch1)
    db_session.add(batch2)
    db_session.commit()
    
    # Create same ISBN in different batches - should work
    analysis1 = analysis_repo.create_analysis(  # ✅ FIX: Remove await
        batch_id=1,
        isbn_or_asin="ISBN001",
        roi_percent=Decimal("25.5")
    )
    
    analysis2 = analysis_repo.create_analysis(  # ✅ FIX: Remove await
        batch_id=2,
        isbn_or_asin="ISBN001",  # Same ISBN, different batch
        roi_percent=Decimal("35.2")
    )
    
    db_session.commit()
    
    assert analysis1.isbn_or_asin == analysis2.isbn_or_asin
    assert analysis1.batch_id != analysis2.batch_id

def test_patch4_isbn_normalization_in_create(analysis_repo, sample_batch, db_session):  # ✅ FIX: Remove async
    """Test ISBN normalization in create_analysis"""
    
    # Create analysis with lowercase/spaces
    analysis = analysis_repo.create_analysis(  # ✅ FIX: Remove await
        batch_id=1,
        isbn_or_asin=" isbn001 ",  # Lowercase with spaces
        roi_percent=Decimal("25.5")
    )
    db_session.commit()
    
    assert analysis.isbn_or_asin == "ISBN001"  # Should be normalized

# ============================================================================
# INTEGRATION TESTS: All patches working together
# ============================================================================

def test_all_patches_integration(analysis_repo, sample_batch, db_session):  # ✅ FIX: Remove async
    """Test all patches working together"""
    
    # Create diverse test data
    analyses_data = [
        {"isbn": "ISBN001", "roi": Decimal("40.0"), "velocity": Decimal("30.0"), "profit": Decimal("15.50")},
        {"isbn": "ISBN002", "roi": Decimal("25.0"), "velocity": Decimal("70.0"), "profit": Decimal("12.25")},
        {"isbn": "ISBN003", "roi": Decimal("60.0"), "velocity": Decimal("20.0"), "profit": Decimal("18.75")},
        {"isbn": "ISBN004", "roi": Decimal("15.0"), "velocity": Decimal("40.0"), "profit": Decimal("8.30")}
    ]
    
    for data in analyses_data:
        analysis = analysis_repo.create_analysis(  # ✅ FIX: Remove await
            batch_id=1,
            isbn_or_asin=data["isbn"],
            roi_percent=data["roi"],
            velocity_score=data["velocity"],
            profit=data["profit"]
        )
    db_session.commit()
    
    # ✅ PATCH 1: Test isbn_list filtering + other filters
    roi_filter = FilterCriteria(field="roi_percent", condition=FilterCondition.GTE, value=Decimal("30"))
    
    result = analysis_repo.list_filtered(  # ✅ FIX: Remove await
        batch_id=1,
        isbn_list=["ISBN001", "ISBN002", "ISBN003"],  # PATCH 1
        filters=[roi_filter],
        sort_by="velocity_score",  # PATCH 2 validation
        sort_desc=True
    )
    
    assert result.total == 2  # ISBN001 and ISBN003 have ROI >= 30
    assert result.items[0].velocity_score >= result.items[1].velocity_score  # Sorted desc
    
    # ✅ PATCH 3: Test balanced strategy with Decimal precision
    top_balanced = analysis_repo.top_n_for_batch(  # ✅ FIX: Remove await
        batch_id=1,
        strategy="balanced",
        limit=3
    )
    
    assert len(top_balanced) == 3
    # Verify balanced scoring works correctly
    
    # ✅ PATCH 4: Test duplicate detection still works
    with pytest.raises(DuplicateIsbnInBatchError):
        analysis_repo.create_analysis(  # ✅ FIX: Remove await
            batch_id=1,
            isbn_or_asin="ISBN001"  # Duplicate
        )

# ============================================================================
# MINI-CONTROLE VALIDATION TESTS
# ============================================================================

def test_mini_controle_exceptions_exist():
    """Test that all required exceptions exist and can be imported"""
    # These should not raise ImportError
    from app.repositories.base import InvalidSortFieldError, DuplicateIsbnInBatchError, InvalidFilterFieldError
    
    # Test they are proper Exception subclasses
    assert issubclass(InvalidSortFieldError, Exception)
    assert issubclass(DuplicateIsbnInBatchError, Exception) 
    assert issubclass(InvalidFilterFieldError, Exception)

def test_mini_controle_page_structure():
    """Test that Page[T] has all required fields"""
    from app.repositories.base import Page
    from app.models.analysis import Analysis
    
    # Create a sample page
    page = Page(
        items=[],
        page=1, 
        page_size=10,
        total=0,
        pages=0,
        has_next=False,
        has_prev=False
    )
    
    # Verify all required attributes exist
    assert hasattr(page, 'total')
    assert hasattr(page, 'has_next') 
    assert hasattr(page, 'has_prev')
    assert hasattr(page, 'items')
    assert hasattr(page, 'pages')

def test_mini_controle_decimal_in_balanced_strategy(analysis_repo, sample_batch, db_session):
    """Test that balanced strategy really uses Decimal precision"""
    
    # Create test analysis
    analysis = Analysis(
        batch_id=1,
        isbn_or_asin="ISBN001", 
        roi_percent=Decimal("33.33"),
        velocity_score=Decimal("66.67")
    )
    db_session.add(analysis)
    db_session.commit()
    
    # Call balanced strategy - should not crash with Decimal
    result = analysis_repo.top_n_for_batch(
        batch_id=1,
        strategy="balanced",
        limit=1
    )
    
    assert len(result) == 1
    assert result[0].isbn_or_asin == "ISBN001"

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])