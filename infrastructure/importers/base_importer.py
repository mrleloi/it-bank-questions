"""Base importer class."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ImportResult:
    """Result of import operation."""
    
    file_path: str
    total_items: int = 0
    imported: int = 0
    skipped: int = 0
    failed: int = 0
    errors: List[Dict[str, Any]] = None
    processing_time_seconds: float = 0.0
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_items == 0:
            return 0.0
        return (self.imported / self.total_items) * 100
    
    def add_error(self, item_id: str, error: str, details: Optional[Dict[str, Any]] = None):
        """Add error to results."""
        self.errors.append({
            'item_id': item_id,
            'error': error,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        })
        self.failed += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'file_path': self.file_path,
            'total_items': self.total_items,
            'imported': self.imported,
            'skipped': self.skipped,
            'failed': self.failed,
            'success_rate': self.success_rate,
            'processing_time_seconds': self.processing_time_seconds,
            'errors': self.errors[:10]  # Limit errors to first 10
        }


@dataclass 
class ImportContext:
    """Context for import operation."""
    
    file_path: Path
    dry_run: bool = False
    batch_size: int = 50
    validate_only: bool = False
    source: str = "imported"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseImporter(ABC):
    """Base class for all importers."""
    
    def __init__(self, batch_size: int = 50):
        self.batch_size = batch_size
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def validate_file(self, file_path: Path) -> bool:
        """Validate if file can be imported."""
        pass
    
    @abstractmethod
    def parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse file and return list of items."""
        pass
    
    @abstractmethod
    def validate_item(self, item: Dict[str, Any]) -> List[str]:
        """Validate single item and return list of validation errors."""
        pass
    
    @abstractmethod
    async def import_item(self, item: Dict[str, Any], context: ImportContext) -> bool:
        """Import single item. Return True if successful."""
        pass
    
    @abstractmethod
    async def item_exists(self, item: Dict[str, Any]) -> bool:
        """Check if item already exists."""
        pass
    
    async def import_file(self, context: ImportContext) -> ImportResult:
        """Import entire file."""
        start_time = datetime.now()
        result = ImportResult(file_path=str(context.file_path))
        
        try:
            # Validate file
            if not self.validate_file(context.file_path):
                result.add_error('file', f'Invalid file format: {context.file_path}')
                return result
            
            # Parse file
            self.logger.info(f"Parsing file: {context.file_path}")
            items = self.parse_file(context.file_path)
            result.total_items = len(items)
            
            if not items:
                self.logger.warning(f"No items found in file: {context.file_path}")
                return result
            
            self.logger.info(f"Found {len(items)} items to import")
            
            # Process in batches
            for i in range(0, len(items), self.batch_size):
                batch = items[i:i + self.batch_size]
                batch_result = await self._process_batch(batch, context)
                
                # Merge batch results
                result.imported += batch_result['imported']
                result.skipped += batch_result['skipped'] 
                result.errors.extend(batch_result['errors'])
                
                self.logger.info(
                    f"Processed batch {i//self.batch_size + 1}: "
                    f"{batch_result['imported']} imported, "
                    f"{batch_result['skipped']} skipped, "
                    f"{len(batch_result['errors'])} errors"
                )
            
            # Update final counts
            result.failed = len(result.errors)
            
        except Exception as e:
            self.logger.error(f"Import failed: {e}", exc_info=True)
            result.add_error('import', f'Import process failed: {str(e)}')
        
        # Calculate processing time
        end_time = datetime.now()
        result.processing_time_seconds = (end_time - start_time).total_seconds()
        
        self.logger.info(
            f"Import completed: {result.imported} imported, "
            f"{result.skipped} skipped, {result.failed} failed "
            f"({result.success_rate:.1f}% success rate)"
        )
        
        return result
    
    async def _process_batch(
        self, 
        batch: List[Dict[str, Any]], 
        context: ImportContext
    ) -> Dict[str, Any]:
        """Process a batch of items."""
        imported = 0
        skipped = 0
        errors = []
        
        for item in batch:
            try:
                item_id = self._get_item_id(item)
                
                # Validate item
                validation_errors = self.validate_item(item)
                if validation_errors:
                    errors.append({
                        'item_id': item_id,
                        'error': 'Validation failed',
                        'details': {'validation_errors': validation_errors}
                    })
                    continue
                
                # Check if item exists
                if await self.item_exists(item):
                    skipped += 1
                    continue
                
                # Skip import in dry run mode
                if context.dry_run or context.validate_only:
                    imported += 1
                    continue
                
                # Import item
                success = await self.import_item(item, context)
                if success:
                    imported += 1
                else:
                    errors.append({
                        'item_id': item_id,
                        'error': 'Import failed',
                        'details': {}
                    })
                
            except Exception as e:
                item_id = self._get_item_id(item)
                errors.append({
                    'item_id': item_id,
                    'error': str(e),
                    'details': {'exception': e.__class__.__name__}
                })
                self.logger.error(f"Failed to process item {item_id}: {e}")
        
        return {
            'imported': imported,
            'skipped': skipped,
            'errors': errors
        }
    
    def _get_item_id(self, item: Dict[str, Any]) -> str:
        """Get unique identifier for item."""
        return item.get('id', item.get('external_id', 'unknown'))
    
    async def validate_file_only(self, file_path: Path) -> ImportResult:
        """Validate file without importing."""
        context = ImportContext(
            file_path=file_path,
            validate_only=True
        )
        return await self.import_file(context)
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions."""
        return []
    
    def get_import_stats(self) -> Dict[str, Any]:
        """Get importer statistics."""
        return {
            'batch_size': self.batch_size,
            'supported_extensions': self.get_supported_extensions(),
        }