import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import models and repositories with corrected paths
from backend.app.models import Base, User, UserRole, Batch, BatchStatus, Analysis
from backend.app.repositories.analysis import AnalysisRepository

@pytest.fixture(scope="session")
def engine():
    """Create test database engine"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Create all tables from shared Base
    Base.metadata.create_all(engine)
    
    yield engine
    engine.dispose()

@pytest.fixture
def db_session(engine):
    """Create database session for each test"""
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    session = Session()
    
    yield session
    
    session.rollback()
    session.close()

class TestSmokeLocal:
    """✅ Smoke test: création user → batch → 3 analyses → list/filter/delete"""
    
    def test_complete_workflow_smoke(self, db_session):
        """Test complet du workflow business"""
        
        # ✅ STEP 1: Créer utilisateur
        user = User(
            email="testuser@arbitragevault.com",
            name="Test Sourcer",
            role=UserRole.SOURCER
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == "testuser@arbitragevault.com"
        
        # ✅ STEP 2: Créer batch
        batch = Batch(
            name="Smoke Test Batch",
            status=BatchStatus.RUNNING,
            items_total=3,
            items_processed=0
        )
        db_session.add(batch)
        db_session.commit()
        
        assert batch.id is not None
        assert batch.status == BatchStatus.RUNNING
        
        # ✅ STEP 3: Créer repository et 3 analyses
        analysis_repo = AnalysisRepository(db_session)
        
        analyses_data = [
            {
                "isbn": "ISBN001",
                "title": "Advanced Python Programming",
                "roi": Decimal("45.5"),
                "velocity": Decimal("72.3"),
                "profit": Decimal("18.75"),
                "price": Decimal("35.99"),
                "bsr": 15420
            },
            {
                "isbn": "ISBN002", 
                "title": "Data Structures & Algorithms",
                "roi": Decimal("32.1"),
                "velocity": Decimal("58.9"),
                "profit": Decimal("12.45"),
                "price": Decimal("42.50"),
                "bsr": 28750
            },
            {
                "isbn": "ISBN003",
                "title": "Machine Learning Fundamentals", 
                "roi": Decimal("67.8"),
                "velocity": Decimal("41.2"),
                "profit": Decimal("25.30"),
                "price": Decimal("29.99"),
                "bsr": 8950
            }
        ]
        
        created_analyses = []
        for data in analyses_data:
            analysis = analysis_repo.create_analysis(
                batch_id=batch.id,
                isbn_or_asin=data["isbn"],
                title=data["title"],
                roi_percent=data["roi"],
                velocity_score=data["velocity"],
                profit=data["profit"],
                current_price=data["price"],
                bsr=data["bsr"]
            )
            created_analyses.append(analysis)
        
        db_session.commit()
        
        # Vérifier création
        assert len(created_analyses) == 3
        for analysis in created_analyses:
            assert analysis.id is not None
            assert analysis.batch_id == batch.id
        
        # ✅ STEP 4: Test list_filtered (base)
        page = analysis_repo.list_filtered(
            batch_id=batch.id,
            page=1,
            page_size=10
        )
        
        assert page.total == 3
        assert len(page.items) == 3
        assert not page.has_next
        assert not page.has_prev
        assert page.pages == 1
        
        # ✅ STEP 5: Test filtering par ROI threshold
        from backend.app.repositories.base import FilterCriteria, FilterCondition
        
        roi_filter = FilterCriteria(
            field="roi_percent",
            condition=FilterCondition.GTE,
            value=Decimal("40.0")
        )
        
        filtered_page = analysis_repo.list_filtered(
            batch_id=batch.id,
            filters=[roi_filter]
        )
        
        # Devrait retourner ISBN001 (45.5%) et ISBN003 (67.8%)
        assert filtered_page.total == 2
        high_roi_isbns = {item.isbn_or_asin for item in filtered_page.items}
        assert high_roi_isbns == {"ISBN001", "ISBN003"}
        
        # ✅ STEP 6: Test ISBN list filtering (PATCH 1)
        isbn_page = analysis_repo.list_filtered(
            batch_id=batch.id,
            isbn_list=["ISBN001", "ISBN002"]  # Exclut ISBN003
        )
        
        assert isbn_page.total == 2
        isbn_filtered = {item.isbn_or_asin for item in isbn_page.items}
        assert isbn_filtered == {"ISBN001", "ISBN002"}
        
        # ✅ STEP 7: Test sorting par velocity_score desc (PATCH 2)
        sorted_page = analysis_repo.list_filtered(
            batch_id=batch.id,
            sort_by="velocity_score",
            sort_desc=True
        )
        
        assert sorted_page.total == 3
        # Ordre attendu: ISBN001 (72.3), ISBN002 (58.9), ISBN003 (41.2)
        assert sorted_page.items[0].isbn_or_asin == "ISBN001"
        assert sorted_page.items[1].isbn_or_asin == "ISBN002" 
        assert sorted_page.items[2].isbn_or_asin == "ISBN003"
        
        # ✅ STEP 8: Test top_n_for_batch strategies (PATCH 3)
        
        # ROI strategy - ISBN003 first (67.8%)
        top_roi = analysis_repo.top_n_for_batch(
            batch_id=batch.id,
            strategy="roi",
            limit=2
        )
        assert len(top_roi) == 2
        assert top_roi[0].isbn_or_asin == "ISBN003"  # 67.8% ROI
        
        # Velocity strategy - ISBN001 first (72.3)
        top_velocity = analysis_repo.top_n_for_batch(
            batch_id=batch.id,
            strategy="velocity", 
            limit=2
        )
        assert len(top_velocity) == 2
        assert top_velocity[0].isbn_or_asin == "ISBN001"  # 72.3 velocity
        
        # Balanced strategy (60% ROI + 40% velocity) - PATCH 3
        # ISBN001: 45.5 * 0.6 + 72.3 * 0.4 = 27.3 + 28.92 = 56.22
        # ISBN002: 32.1 * 0.6 + 58.9 * 0.4 = 19.26 + 23.56 = 42.82
        # ISBN003: 67.8 * 0.6 + 41.2 * 0.4 = 40.68 + 16.48 = 57.16
        # Ordre: ISBN003 (57.16), ISBN001 (56.22), ISBN002 (42.82)
        top_balanced = analysis_repo.top_n_for_batch(
            batch_id=batch.id,
            strategy="balanced",
            limit=3
        )
        assert len(top_balanced) == 3
        assert top_balanced[0].isbn_or_asin == "ISBN003"  # Highest balanced score
        
        # ✅ STEP 9: Test count_by_thresholds
        thresholds = analysis_repo.count_by_thresholds(
            batch_id=batch.id,
            roi_threshold=Decimal("40.0"),
            velocity_threshold=Decimal("60.0"),
            profit_threshold=Decimal("15.0")
        )
        
        assert thresholds["total"] == 3
        assert thresholds["high_roi"] == 2  # ISBN001, ISBN003
        assert thresholds["high_velocity"] == 1  # ISBN001 only
        assert thresholds["high_profit"] == 2  # ISBN001, ISBN003
        # Golden: ROI>=40 AND velocity>=60 AND profit>=15 -> only ISBN001
        assert thresholds["golden"] == 1
        
        # ✅ STEP 10: Test delete operations
        
        # Delete par ID
        analysis_to_delete = created_analyses[0]  # ISBN001
        deleted_count = analysis_repo.delete_by_ids([analysis_to_delete.id])
        
        assert deleted_count == 1
        
        # Vérifier suppression
        remaining_page = analysis_repo.list_filtered(batch_id=batch.id)
        assert remaining_page.total == 2
        remaining_isbns = {item.isbn_or_asin for item in remaining_page.items}
        assert remaining_isbns == {"ISBN002", "ISBN003"}  # ISBN001 supprimé
        
        # Delete all remaining by batch
        deleted_batch_count = analysis_repo.delete_by_batch(batch.id)
        assert deleted_batch_count == 2
        
        # Vérifier batch vide
        empty_page = analysis_repo.list_filtered(batch_id=batch.id)
        assert empty_page.total == 0
        assert len(empty_page.items) == 0
        
        print("✅ SMOKE TEST COMPLET - Tous les workflows validés !")
        
    def test_patch4_duplicate_detection(self, db_session):
        """Test PATCH 4: DuplicateIsbnInBatchError detection"""
        
        # Créer batch
        batch = Batch(name="Duplicate Test", status=BatchStatus.RUNNING)
        db_session.add(batch)
        db_session.commit()
        
        analysis_repo = AnalysisRepository(db_session)
        
        # Créer première analyse
        analysis1 = analysis_repo.create_analysis(
            batch_id=batch.id,
            isbn_or_asin="TESTISBN001",
            roi_percent=Decimal("25.0")
        )
        db_session.commit()
        
        # Tenter de créer duplicate - devrait lever exception
        from backend.app.repositories.base import DuplicateIsbnInBatchError
        
        with pytest.raises(DuplicateIsbnInBatchError) as exc_info:
            analysis_repo.create_analysis(
                batch_id=batch.id,
                isbn_or_asin="TESTISBN001",  # Même ISBN, même batch
                roi_percent=Decimal("35.0")
            )
        
        assert "TESTISBN001" in str(exc_info.value)
        assert "batch" in str(exc_info.value).lower()
        
        print("✅ PATCH 4 - DuplicateIsbnInBatchError validation OK")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
