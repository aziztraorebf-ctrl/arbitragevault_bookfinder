# Changelog

All notable changes to ArbitrageVault BookFinder will be documented in this file.

## [1.3.0] - 2025-08-20

### 🚀 FastAPI Integration Complete - Production Ready REST API

#### 🔥 Core API Endpoints
- **`POST /api/v1/analyses`** - Create analysis with validation (admin/internal)
- **`GET /api/v1/analyses`** - Advanced filtering (ROI, velocity, profit, ISBN lists)
- **`GET /api/v1/analyses/top`** - Strategic top N (roi|velocity|profit|balanced)
- **`GET /api/v1/batches`** - List with progress metrics (progress_percent, items_remaining)
- **`PATCH /api/v1/batches/{id}/status`** - Status updates with validation
- **`GET /api/v1/health/`** - Basic + database health checks

#### 🏗️ Technical Architecture
- **Exception Mapping**: InvalidSortFieldError→422, DuplicateIsbnInBatchError→409, NotFoundError→404
- **Request/Response Models**: PageOut[T], AnalysisOut, BatchOut with Pydantic validation
- **Database Integration**: 1 session per request via yield pattern
- **Middleware Stack**: Error handling, request logging, CORS configuration

#### 📊 Business Logic Integration  
- **Repository Layer Features**: All v1.2.5 Patch Pack features exposed through API
- **Strategic Analysis**: Balanced strategy (60% ROI + 40% velocity) via endpoints
- **Advanced Filtering**: Multi-criteria queries for golden opportunities
- **ISBN Processing**: Automatic normalization and duplicate detection

#### 🧪 Comprehensive Testing
- **25+ test cases** covering all endpoints and error scenarios
- **FastAPI TestClient** integration with repository layer validation
- **Business logic tests**: ROI filtering, balanced scoring, status transitions
- **Error handling verification**: All HTTP status codes properly tested

#### 🔧 Development & Production Support
- **Development Tools**: run_dev.py, .env.development, auto table creation
- **Production Configuration**: Environment-based config, CORS restrictions, health monitoring
- **API Documentation**: OpenAPI/Swagger (/docs), ReDoc (/redoc), comprehensive README
- **Performance**: Connection pooling, database indexes, efficient pagination

#### 📈 Performance & Scalability
- **Database Optimization**: Repository layer indexes maintained, stable sorting
- **Error Handling**: Graceful degradation, structured logging, transaction rollback
- **Configuration Management**: Pydantic Settings with environment variables
- **Deployment Ready**: Docker structure, health checks, production WSGI support

### Technical Details
- **FastAPI Framework**: Production-ready REST API with auto-generated documentation
- **Integration**: Zero breaking changes to v1.2.5 repository layer
- **Testing**: Comprehensive test suite with in-memory SQLite isolation
- **Architecture**: Clean separation (routers, schemas, dependencies, middleware)

### Files Added
```
backend/app/main.py - FastAPI application with middleware
backend/app/api/v1/routers/ - All endpoint implementations  
backend/app/api/v1/schemas/ - Pydantic request/response models
backend/app/core/exceptions.py - HTTP exception mapping
backend/app/core/middleware.py - Error handling & logging
backend/run_dev.py - Development server script
backend/tests/test_fastapi_endpoints.py - 25+ test cases
backend/README_FASTAPI.md - Complete API documentation
```

---

## [1.2.5] - 2025-08-20

### ✅ Repository Layer Complete - Foundation for FastAPI

#### 🔥 Patch Pack Features Added
- **PATCH 1**: `isbn_list` filtering with automatic normalization in `list_filtered()`
- **PATCH 2**: Strict sort field validation with `InvalidSortFieldError`
- **PATCH 3**: Balanced strategy using `literal(Decimal())` for financial precision
- **PATCH 4**: `DuplicateIsbnInBatchError` handling with proper rollback

#### 🏗️ Core Infrastructure  
- **BaseRepository[T]**: Generic repository with advanced pagination (`Page[T]`)
- **AnalysisRepository**: Business logic methods (`top_n_for_batch`, `count_by_thresholds`)
- **Models**: User, Batch, Analysis with proper relationships and constraints
- **Database**: Performance indexes and unique constraints

#### 🧪 Comprehensive Testing
- **15+ test cases** covering all patch functionality
- **Smoke test**: Complete User→Batch→3 Analyses→List/Filter/Delete workflow
- **Integration tests** ensuring patches work together
- **Automated validation script** (`validate_v1_2_5.py`)

#### ⚙️ Configuration & Infrastructure
- **Pydantic settings** with environment variables support
- **Database core** with FastAPI-ready dependencies (`get_db()`)
- **Performance indexes** for production-scale queries
- **Tech debt documented** (`expire_on_commit=False`)

#### 🎯 Business Logic Delivered
- **Strategy methods**: ROI, Velocity, Profit, Balanced (60% ROI + 40% velocity)
- **Advanced filtering**: Multi-criteria with ISBN lists
- **Golden opportunities**: High ROI + high velocity + high profit
- **Bulk operations**: Efficient delete by batch or ID list

---

## [Upcoming 1.4.0] - Keepa API Integration

### Planned Features
- Real-time data fetching from Keepa API
- Background job processing for large batches
- WebSocket updates for progress tracking
- Enhanced analysis with live market data

---

**Legend**: ✅ Complete | 🔥 Major Feature | 🏗️ Infrastructure | 🧪 Testing | ⚙️ Configuration | 🎯 Business Logic | 📊 Integration