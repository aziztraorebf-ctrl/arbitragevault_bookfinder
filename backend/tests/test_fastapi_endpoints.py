import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from decimal import Decimal
import json

from backend.app.main import create_app
from backend.app.models import Base, User, UserRole, Batch, BatchStatus, Analysis
from backend.app.api.v1.deps.database import get_sync_db_dependency

@pytest.fixture(scope="session")
def engine():
    """Create test database engine"""
    engine = create_engine("sqlite:///:memory:", echo=False)
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

@pytest.fixture
def client(db_session):
    """Create test client with database dependency override"""
    app = create_app()
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_sync_db_dependency] = override_get_db
    
    with TestClient(app) as client:
        yield client

@pytest.fixture
def sample_data(db_session):
    """Create sample data for testing"""
    # Create user
    user = User(
        email="test@arbitragevault.com",
        name="Test User",
        role=UserRole.ADMIN
    )
    db_session.add(user)
    
    # Create batch
    batch = Batch(
        id=1,
        name="Test Batch",
        status=BatchStatus.RUNNING,
        items_total=3,
        items_processed=1
    )
    db_session.add(batch)
    
    # Create analyses
    analyses = [
        Analysis(
            batch_id=1,
            isbn_or_asin="ISBN001",
            title="Test Book 1",
            roi_percent=Decimal("45.5"),
            velocity_score=Decimal("72.3"),
            profit=Decimal("18.75"),
            current_price=Decimal("35.99"),
            bsr=15420
        ),
        Analysis(
            batch_id=1,
            isbn_or_asin="ISBN002", 
            title="Test Book 2",
            roi_percent=Decimal("32.1"),
            velocity_score=Decimal("58.9"),
            profit=Decimal("12.45"),
            current_price=Decimal("42.50"),
            bsr=28750
        ),
        Analysis(
            batch_id=1,
            isbn_or_asin="ISBN003",
            title="Test Book 3", 
            roi_percent=Decimal("67.8"),
            velocity_score=Decimal("41.2"),
            profit=Decimal("25.30"),
            current_price=Decimal("29.99"),
            bsr=8950
        )
    ]
    
    for analysis in analyses:
        db_session.add(analysis)
    
    db_session.commit()
    
    return {
        "user": user,
        "batch": batch,
        "analyses": analyses
    }

class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_health_check(self, client):
        """Test basic health check"""
        response = client.get("/api/v1/health/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data
    
    def test_database_health_check(self, client, sample_data):
        """Test database health check"""
        response = client.get("/api/v1/health/db")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert "response_time_ms" in data

class TestAnalysisEndpoints:
    """Test analysis endpoints"""
    
    def test_create_analysis(self, client, sample_data):
        """Test POST /api/v1/analyses"""
        analysis_data = {
            "batch_id": 1,
            "isbn_or_asin": "ISBN004",
            "title": "New Test Book",
            "roi_percent": 55.5,
            "velocity_score": 65.0,
            "profit": 20.00,
            "current_price": 30.00,
            "bsr": 12000
        }
        
        response = client.post("/api/v1/analyses/", json=analysis_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["isbn_or_asin"] == "ISBN004"  # Normalized
        assert data["title"] == "New Test Book"
        assert float(data["roi_percent"]) == 55.5
        assert "id" in data
    
    def test_create_analysis_duplicate_error(self, client, sample_data):
        """Test duplicate ISBN detection"""
        analysis_data = {
            "batch_id": 1,
            "isbn_or_asin": "ISBN001",  # Already exists
            "title": "Duplicate Book",
            "roi_percent": 25.0
        }
        
        response = client.post("/api/v1/analyses/", json=analysis_data)
        assert response.status_code == 409  # Conflict
        
        data = response.json()
        assert data["error"] == "duplicate_isbn"
        assert "ISBN001" in data["message"]
    
    def test_list_analyses_basic(self, client, sample_data):
        """Test GET /api/v1/analyses basic listing"""
        response = client.get("/api/v1/analyses/?batch_id=1")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3
        assert data["page"] == 1
        assert data["has_next"] == False
        assert data["has_prev"] == False
    
    def test_list_analyses_with_filters(self, client, sample_data):
        """Test GET /api/v1/analyses with ROI filter"""
        response = client.get("/api/v1/analyses/?batch_id=1&min_roi=40.0")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 2  # ISBN001 (45.5%) and ISBN003 (67.8%)
        
        # Verify all returned items have ROI >= 40
        for item in data["items"]:
            assert float(item["roi_percent"]) >= 40.0
    
    def test_list_analyses_with_isbn_list(self, client, sample_data):
        """Test ISBN list filtering"""
        response = client.get("/api/v1/analyses/?batch_id=1&isbn_list=ISBN001,ISBN003")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 2
        
        isbns = {item["isbn_or_asin"] for item in data["items"]}
        assert isbns == {"ISBN001", "ISBN003"}
    
    def test_list_analyses_with_sorting(self, client, sample_data):
        """Test sorting by velocity_score desc"""
        response = client.get("/api/v1/analyses/?batch_id=1&sort=velocity_score&sort_desc=true")
        assert response.status_code == 200
        
        data = response.json()
        items = data["items"]
        
        # Should be sorted: ISBN001 (72.3), ISBN002 (58.9), ISBN003 (41.2)
        assert items[0]["isbn_or_asin"] == "ISBN001"
        assert items[1]["isbn_or_asin"] == "ISBN002"
        assert items[2]["isbn_or_asin"] == "ISBN003"
    
    def test_list_analyses_invalid_sort_field(self, client, sample_data):
        """Test invalid sort field error"""
        response = client.get("/api/v1/analyses/?batch_id=1&sort=invalid_field")
        assert response.status_code == 422
        
        data = response.json()
        assert data["error"] == "invalid_sort_field"
        assert "invalid_field" in data["message"]
    
    def test_get_top_analyses_balanced(self, client, sample_data):
        """Test GET /api/v1/analyses/top with balanced strategy"""
        response = client.get("/api/v1/analyses/top?batch_id=1&n=2&strategy=balanced")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        
        # Based on balanced scoring (60% ROI + 40% velocity)
        # ISBN003 should be first (67.8*0.6 + 41.2*0.4 = 57.16)
        # ISBN001 should be second (45.5*0.6 + 72.3*0.4 = 56.22)
        assert data[0]["isbn_or_asin"] == "ISBN003"
    
    def test_get_top_analyses_roi_strategy(self, client, sample_data):
        """Test GET /api/v1/analyses/top with ROI strategy"""
        response = client.get("/api/v1/analyses/top?batch_id=1&n=2&strategy=roi")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        
        # ROI strategy: ISBN003 (67.8%) should be first
        assert data[0]["isbn_or_asin"] == "ISBN003"
        assert float(data[0]["roi_percent"]) == 67.8
    
    def test_get_top_analyses_batch_not_found(self, client, sample_data):
        """Test top analyses with non-existent batch"""
        response = client.get("/api/v1/analyses/top?batch_id=999&strategy=roi")
        assert response.status_code == 404
        
        data = response.json()
        assert data["error"] == "not_found"
        assert "999" in data["message"]

class TestBatchEndpoints:
    """Test batch endpoints"""
    
    def test_list_batches(self, client, sample_data):
        """Test GET /api/v1/batches"""
        response = client.get("/api/v1/batches/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        
        batch = data[0]
        assert batch["id"] == 1
        assert batch["name"] == "Test Batch"
        assert batch["status"] == "RUNNING"
        assert batch["items_total"] == 3
        assert batch["items_processed"] == 1
        assert batch["progress_percent"] == 33.3
        assert batch["items_remaining"] == 2
    
    def test_get_batch_stats(self, client, sample_data):
        """Test GET /api/v1/batches/stats"""
        response = client.get("/api/v1/batches/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_batches"] == 1
        assert data["total_analyses"] == 3
        assert data["running_batches"] == 1
        assert data["latest_batch_id"] == 1
        assert "batches_by_status" in data
        assert data["batches_by_status"]["RUNNING"] == 1
    
    def test_update_batch_status_valid_transition(self, client, sample_data):
        """Test PATCH /api/v1/batches/{id}/status valid transition"""
        update_data = {
            "status": "DONE",
            "items_processed": 3
        }
        
        response = client.patch("/api/v1/batches/1/status", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "DONE"
        assert data["items_processed"] == 3
        assert data["progress_percent"] == 100.0
        assert data["finished_at"] is not None
    
    def test_update_batch_status_invalid_transition(self, client, sample_data):
        """Test invalid status transition"""
        update_data = {"status": "PENDING"}  # RUNNING -> PENDING not allowed
        
        response = client.patch("/api/v1/batches/1/status", json=update_data)
        assert response.status_code == 422
        
        data = response.json()
        assert data["error"] == "invalid_status_transition"
        assert "RUNNING" in data["message"]
        assert "PENDING" in data["message"]
    
    def test_get_batch_by_id(self, client, sample_data):
        """Test GET /api/v1/batches/{id}"""
        response = client.get("/api/v1/batches/1")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Test Batch"
        assert data["status"] == "RUNNING"
    
    def test_get_batch_not_found(self, client, sample_data):
        """Test batch not found"""
        response = client.get("/api/v1/batches/999")
        assert response.status_code == 404
        
        data = response.json()
        assert data["error"] == "not_found"
        assert "999" in data["message"]

class TestRootEndpoint:
    """Test root endpoint"""
    
    def test_root_endpoint(self, client):
        """Test GET / root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "ArbitrageVault BookFinder API" in data["message"]
        assert data["status"] == "running"
        assert "version" in data

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
