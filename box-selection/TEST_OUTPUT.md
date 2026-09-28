# Test Output

```
$ python manage.py test -v 2
Found 61 test(s).
Creating test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Operations to perform:
  Synchronize unmigrated apps: messages, staticfiles
  Apply all migrations: admin, auth, boxes, contenttypes, sessions
Synchronizing apps without migrations:
  Creating tables...
    Running deferred SQL...
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying admin.0003_logentry_add_action_flag_choices... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying auth.0009_alter_user_last_name_max_length... OK
  Applying auth.0010_alter_group_name_max_length... OK
  Applying auth.0011_update_proxy_permissions... OK
  Applying auth.0012_alter_user_first_name_max_length... OK
  Applying boxes.0001_initial... OK
  Applying sessions.0001_initial... OK
System check identified no issues (0 silenced).
test_body_not_an_object (boxes.tests.test_api.RecommendBoxApiTests.test_body_not_an_object) ... ok
test_boolean_quantity_rejected (boxes.tests.test_api.RecommendBoxApiTests.test_boolean_quantity_rejected) ... ok
test_duplicate_lines_are_merged (boxes.tests.test_api.RecommendBoxApiTests.test_duplicate_lines_are_merged) ... ok
test_each_item_fits_but_not_together (boxes.tests.test_api.RecommendBoxApiTests.test_each_item_fits_but_not_together) ... ok
test_empty_body (boxes.tests.test_api.RecommendBoxApiTests.test_empty_body) ... ok
test_empty_items (boxes.tests.test_api.RecommendBoxApiTests.test_empty_items) ... ok
test_fractional_quantity (boxes.tests.test_api.RecommendBoxApiTests.test_fractional_quantity) ... ok
test_get_not_allowed (boxes.tests.test_api.RecommendBoxApiTests.test_get_not_allowed) ... ok
test_heavy_item_picks_cheapest_box_with_capacity (boxes.tests.test_api.RecommendBoxApiTests.test_heavy_item_picks_cheapest_box_with_capacity) ... ok
test_invalid_json (boxes.tests.test_api.RecommendBoxApiTests.test_invalid_json) ... ok
test_item_not_an_object (boxes.tests.test_api.RecommendBoxApiTests.test_item_not_an_object) ... ok
test_item_too_big_for_any_box (boxes.tests.test_api.RecommendBoxApiTests.test_item_too_big_for_any_box) ... ok
test_laptop_sleeve_needs_medium (boxes.tests.test_api.RecommendBoxApiTests.test_laptop_sleeve_needs_medium) ... ok
test_long_lamp_needs_large (boxes.tests.test_api.RecommendBoxApiTests.test_long_lamp_needs_large) ... ok
test_missing_items (boxes.tests.test_api.RecommendBoxApiTests.test_missing_items) ... ok
test_mixed_order (boxes.tests.test_api.RecommendBoxApiTests.test_mixed_order) ... ok
test_negative_quantity (boxes.tests.test_api.RecommendBoxApiTests.test_negative_quantity) ... ok
test_no_boxes_configured (boxes.tests.test_api.RecommendBoxApiTests.test_no_boxes_configured) ... ok
test_order_too_heavy_for_any_box (boxes.tests.test_api.RecommendBoxApiTests.test_order_too_heavy_for_any_box) ... ok
test_single_book_goes_in_small_box (boxes.tests.test_api.RecommendBoxApiTests.test_single_book_goes_in_small_box) ... ok
test_six_mugs_need_medium (boxes.tests.test_api.RecommendBoxApiTests.test_six_mugs_need_medium) ... ok
test_string_product_id (boxes.tests.test_api.RecommendBoxApiTests.test_string_product_id) ... ok
test_too_many_units (boxes.tests.test_api.RecommendBoxApiTests.test_too_many_units) ... ok
test_two_books_still_fit_small (boxes.tests.test_api.RecommendBoxApiTests.test_two_books_still_fit_small) ... ok
test_unknown_product (boxes.tests.test_api.RecommendBoxApiTests.test_unknown_product) ... ok
test_zero_quantity (boxes.tests.test_api.RecommendBoxApiTests.test_zero_quantity) ... ok
test_database_rejects_zero_max_weight (boxes.tests.test_models.BoxModelTests.test_database_rejects_zero_max_weight) ... ok
test_to_spec (boxes.tests.test_models.BoxModelTests.test_to_spec) ... ok
test_validation_rejects_negative_cost (boxes.tests.test_models.BoxModelTests.test_validation_rejects_negative_cost) ... ok
test_database_rejects_negative_weight (boxes.tests.test_models.ProductModelTests.test_database_rejects_negative_weight) ... ok
test_to_spec (boxes.tests.test_models.ProductModelTests.test_to_spec) ... ok
test_validation_rejects_zero_dimension (boxes.tests.test_models.ProductModelTests.test_validation_rejects_zero_dimension) ... ok
test_combined_reason (boxes.tests.test_packing.ExplainNoFitTests.test_combined_reason) ... ok
test_no_boxes (boxes.tests.test_packing.ExplainNoFitTests.test_no_boxes) ... ok
test_oversize_reason (boxes.tests.test_packing.ExplainNoFitTests.test_oversize_reason) ... ok
test_weight_reason (boxes.tests.test_packing.ExplainNoFitTests.test_weight_reason) ... ok
test_item_fits_alone_exact (boxes.tests.test_packing.HelperTests.test_item_fits_alone_exact) ... ok
test_item_fits_alone_needs_rotation (boxes.tests.test_packing.HelperTests.test_item_fits_alone_needs_rotation) ... ok
test_item_too_long_in_every_orientation (boxes.tests.test_packing.HelperTests.test_item_too_long_in_every_orientation) ... ok
test_weight_boundary_is_inclusive (boxes.tests.test_packing.HelperTests.test_weight_boundary_is_inclusive) ... ok
test_random_packings_are_always_valid (boxes.tests.test_packing.PackItemsTests.test_random_packings_are_always_valid)
Whenever the heuristic claims success, the result must be a real packing. ... ok
test_rotation_is_used (boxes.tests.test_packing.PackItemsTests.test_rotation_is_used) ... ok
test_single_item_exact_fit (boxes.tests.test_packing.PackItemsTests.test_single_item_exact_fit) ... ok
test_stacking_uses_height (boxes.tests.test_packing.PackItemsTests.test_stacking_uses_height) ... ok
test_three_cubes_do_not_fit_when_volume_too_small (boxes.tests.test_packing.PackItemsTests.test_three_cubes_do_not_fit_when_volume_too_small) ... ok
test_two_cubes_side_by_side (boxes.tests.test_packing.PackItemsTests.test_two_cubes_side_by_side) ... ok
test_volume_fits_but_shape_blocks (boxes.tests.test_packing.PackItemsTests.test_volume_fits_but_shape_blocks) ... ok
test_cheaper_box_is_not_always_the_smaller_one (boxes.tests.test_packing.SelectBoxTests.test_cheaper_box_is_not_always_the_smaller_one) ... ok
test_cost_tie_prefers_smaller_volume (boxes.tests.test_packing.SelectBoxTests.test_cost_tie_prefers_smaller_volume) ... ok
test_empty_order_rejected (boxes.tests.test_packing.SelectBoxTests.test_empty_order_rejected) ... ok
test_full_tie_is_deterministic_by_name (boxes.tests.test_packing.SelectBoxTests.test_full_tie_is_deterministic_by_name) ... ok
test_negative_cost_rejected (boxes.tests.test_packing.SelectBoxTests.test_negative_cost_rejected) ... ok
test_non_positive_box_rejected (boxes.tests.test_packing.SelectBoxTests.test_non_positive_box_rejected) ... ok
test_non_positive_item_rejected (boxes.tests.test_packing.SelectBoxTests.test_non_positive_item_rejected) ... ok
test_overweight_order (boxes.tests.test_packing.SelectBoxTests.test_overweight_order) ... ok
test_picks_cheapest_fitting_box (boxes.tests.test_packing.SelectBoxTests.test_picks_cheapest_fitting_box) ... ok
test_recommendation_summary_values (boxes.tests.test_packing.SelectBoxTests.test_recommendation_summary_values) ... ok
test_returns_none_when_nothing_fits (boxes.tests.test_packing.SelectBoxTests.test_returns_none_when_nothing_fits) ... ok
test_returns_none_with_no_boxes (boxes.tests.test_packing.SelectBoxTests.test_returns_none_with_no_boxes) ... ok
test_skips_box_that_is_too_light (boxes.tests.test_packing.SelectBoxTests.test_skips_box_that_is_too_light) ... ok
test_skips_box_that_is_too_small (boxes.tests.test_packing.SelectBoxTests.test_skips_box_that_is_too_small) ... ok

----------------------------------------------------------------------
Ran 61 tests in 0.103s

OK
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
```
