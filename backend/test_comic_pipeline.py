import sys, os, dotenv
dotenv.load_dotenv("backend/.env")
sys.path.insert(0, "backend")

from sqlalchemy.orm import sessionmaker
from db.models import Comic, ComicPanel, ComicJob, engine
from agents.pro_comic_agent import ProComicAgent
from services.image_provider import ImageProviderFactory, StabilityImageProvider, ComfyUIProvider

SessionLocal = sessionmaker(bind=engine)

print("=== 1. Testing Database Models & Schema ===")
session = SessionLocal()
test_job = ComicJob(
    id="test_job_001",
    status="pending",
    current_step="Test step",
    progress_percent=10,
    total_panels=6,
    completed_panels=0
)
session.merge(test_job)
session.commit()
fetched_job = session.query(ComicJob).filter(ComicJob.id == "test_job_001").first()
assert fetched_job is not None, "Failed to fetch test job"
assert fetched_job.status == "pending"
print("ComicJob created and retrieved successfully:", fetched_job.id)

print("\n=== 2. Testing ProComicAgent ===")
agent = ProComicAgent()
fallback = agent._get_fallback()
assert len(fallback["character_bible"]) >= 2, "Character bible should have characters"
assert len(fallback["location_bible"]) >= 2, "Location bible should have locations"
assert 10 <= len(fallback["panels"]) <= 16, f"Panels count should be 10-16, got {len(fallback['panels'])}"
p1 = fallback["panels"][0]
assert "dialogue" in p1 and len(p1["dialogue"]) > 0, "Panel 1 should have dialogue"
assert "image_prompt" in p1 and "full color" in p1["image_prompt"].lower(), "Panel 1 prompt should be full color"
print(f"ProComicAgent fallback verified: {len(fallback['panels'])} panels, Character Bible & Location Bible consistent.")

print("\n=== 3. Testing Image Provider Factory ===")
primary = ImageProviderFactory.get_primary_provider()
assert isinstance(primary, StabilityImageProvider), "Primary provider must be StabilityImageProvider"
assert primary.is_available() == True, "Stability AI should be configured"
assert primary.normalize_aspect_ratio("wide") == "16:9"
assert primary.normalize_aspect_ratio("tall") == "2:3"
assert primary.normalize_aspect_ratio("square") == "1:1"
print("StabilityImageProvider verified. Aspect ratios: 16:9, 2:3, 1:1 mapped properly.")

enhancer = ImageProviderFactory.get_local_enhancer()
assert isinstance(enhancer, ComfyUIProvider), "Enhancer must be ComfyUIProvider"
print("ComfyUIProvider verified. is_available non-blocking check:", enhancer.is_available())

# Cleanup test job
session.delete(fetched_job)
session.commit()
session.close()
print("\n>>> ALL PIPELINE TESTS PASSED! <<<")
