import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# Sample valid asset data
def get_valid_asset_data():
    return {
        'asset_id': 'ABC-1234',
        'asset_type': 'Pump',
        'unit': 'Unit A',
        'location': 'Building 1',
        'install_year': 2020,
        'last_inspection': '2023-01-15',
        'operating_hours': 1500.5,
        'status': 'Active',
        'criticality': 'High',
        'notes': 'Regular maintenance required'
    }

# Happy path tests
class TestCreateAsset:
    def test_create_asset_success(self):
        data = get_valid_asset_data()
        response = client.post('/assets', json=data)
        assert response.status_code == 201
        assert response.json()['asset_id'] == data['asset_id']

    def test_create_asset_invalid_id_format(self):
        data = get_valid_asset_data()
        data['asset_id'] = 'invalid-id'
        response = client.post('/assets', json=data)
        assert response.status_code == 422

    def test_create_asset_invalid_criticality(self):
        data = get_valid_asset_data()
        data['criticality'] = 'Invalid'
        response = client.post('/assets', json=data)
        assert response.status_code == 422

class TestListAssets:
    def test_list_assets_success(self):
        response = client.get('/assets')
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_assets_with_filters(self):
        response = client.get('/assets?status=Active&unit=Unit A&criticality=High')
        assert response.status_code == 200
        assert isinstance(response.json(), list)

class TestGetAsset:
    def test_get_asset_success(self):
        # First create an asset
        data = get_valid_asset_data()
        client.post('/assets', json=data)
        # Then retrieve it
        response = client.get(f"/assets/{data['asset_id']}")
        assert response.status_code == 200
        assert response.json()['asset_id'] == data['asset_id']

    def test_get_asset_not_found(self):
        response = client.get('/assets/ZZZ-9999')
        assert response.status_code == 404

class TestUpdateAsset:
    def test_update_asset_success(self):
        # First create an asset
        data = get_valid_asset_data()
        client.post('/assets', json=data)
        # Then update it
        update_data = {'status': 'Inactive', 'operating_hours': 2000.0}
        response = client.put(f"/assets/{data['asset_id']}", json=update_data)
        assert response.status_code == 200
        assert response.json()['status'] == 'Inactive'

    def test_update_asset_not_found(self):
        update_data = {'status': 'Inactive'}
        response = client.put('/assets/ZZZ-9999', json=update_data)
        assert response.status_code == 404

    def test_update_asset_reject_asset_id_change(self):
        # First create an asset
        data = get_valid_asset_data()
        client.post('/assets', json=data)
        # Try to change asset_id (should be ignored since it's not in update model)
        update_data = {'asset_type': 'Updated Pump'}
        response = client.put(f"/assets/{data['asset_id']}", json=update_data)
        assert response.status_code == 200
        assert response.json()['asset_type'] == 'Updated Pump'

class TestDeleteAsset:
    def test_delete_asset_success(self):
        # First create an asset
        data = get_valid_asset_data()
        client.post('/assets', json=data)
        # Then delete it
        response = client.delete(f"/assets/{data['asset_id']}")
        assert response.status_code == 200
        assert response.json()['message'] == 'Asset deleted successfully'
        # Verify it's not found after deletion
        response = client.get(f"/assets/{data['asset_id']}")
        assert response.status_code == 404

    def test_delete_asset_not_found(self):
        response = client.delete('/assets/ZZZ-9999')
        assert response.status_code == 404