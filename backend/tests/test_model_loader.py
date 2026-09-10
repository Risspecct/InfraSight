from app.services.model_loader import (
    load_cost_model,
    load_schedule_model,
)


print("Loading cost model...")

cost_model = load_cost_model()

print("Cost model loaded")
print("Trees:", cost_model.num_trees())
print("Features:", cost_model.num_feature())


print("\nLoading schedule model...")

schedule_artifact = load_schedule_model()

print("Schedule model loaded")
print("Type:", type(schedule_artifact).__name__)
print("Model type:", schedule_artifact["model_type"])
print("Threshold:", schedule_artifact["threshold"])
print("Horizon:", schedule_artifact["horizon"])
print("Features:", len(schedule_artifact["features"]))
