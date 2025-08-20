# Changelog

All notable changes to ArbitrageVault BookFinder will be documented in this file.

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

### Technical Details
- **Database**: SQLAlchemy with composite indexes for balanced strategy
- **Testing**: pytest with in-memory SQLite for comprehensive coverage  
- **Error Handling**: Custom exceptions with proper HTTP mapping ready
- **Performance**: Optimized queries with stable sorting and pagination metadata

### Files Added
```
backend/app/models/ (base.py, user.py, batch.py, analysis.py)
backend/app/repositories/ (base.py, analysis.py)
backend/app/config/ (settings.py)
backend/app/core/ (database.py)
backend/migrations/ (create_indexes.sql)
backend/tests/ (test_patch_pack.py, test_smoke_local.py)
backend/validate_v1_2_5.py
backend/.env.example
```

---

## [Upcoming 1.3.0] - FastAPI Integration

### Planned Features
- REST API endpoints for analysis operations
- Request/response models with Pydantic validation
- Database integration with async session management  
- Error handling middleware with proper HTTP status codes
- OpenAPI documentation generation

---

**Legend**: ✅ Complete | 🔥 Major Feature | 🏗️ Infrastructure | 🧪 Testing | ⚙️ Configuration | 🎯 Business Logic