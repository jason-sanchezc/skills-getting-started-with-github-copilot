"""
Test suite for the Mergington High School Activities API.

Tests follow the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and preconditions
- Act: Execute the API operation being tested
- Assert: Verify the expected outcome
"""

import pytest


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_redirect(self, client):
        """
        Test that the root endpoint redirects to the static index page.

        ARRANGE: Request to /
        ACT: Call GET /
        ASSERT: Verify 307 redirect to /static/index.html
        """
        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivitiesEndpoint:
    """Tests for the GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client, fresh_activities):
        """
        Test that the activities endpoint returns all available activities.

        ARRANGE: (no setup needed)
        ACT: Call GET /activities
        ASSERT: Verify 200 status and 9 activities returned
        """
        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == 9
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities

    def test_get_activities_structure(self, client, fresh_activities):
        """
        Test that activities have the correct structure with all required fields.

        ARRANGE: (no setup)
        ACT: Call GET /activities and inspect first activity
        ASSERT: Verify activity has all required fields
        """
        # Act
        response = client.get("/activities")
        activities = response.json()
        chess_club = activities["Chess Club"]

        # Assert
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)

    def test_activities_have_correct_participant_counts(self, client, fresh_activities):
        """
        Test that activities have the correct initial participant counts.

        ARRANGE: (no setup)
        ACT: Call GET /activities
        ASSERT: Verify participant lists match expected initial data
        """
        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert len(activities["Chess Club"]["participants"]) == 2
        assert "michael@mergington.edu" in activities["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in activities["Chess Club"]["participants"]

        assert len(activities["Programming Class"]["participants"]) == 2
        assert len(activities["Gym Class"]["participants"]) == 2
        assert len(activities["Basketball Team"]["participants"]) == 0


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""

    def test_signup_new_student_success(self, client, fresh_activities):
        """
        Test that a new student can successfully sign up for an activity.

        ARRANGE: Get fresh activities, choose empty activity (Basketball Team)
        ACT: POST signup with new student email
        ASSERT: Verify 200 status and "Signed up" message
        """
        # Arrange
        email = "new_student@mergington.edu"
        activity = "Basketball Team"

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert email in data["message"]
        assert activity in data["message"]

    def test_signup_adds_participant_to_list(self, client, fresh_activities):
        """
        Test that a signed-up student appears in the activity's participant list.

        ARRANGE: Get fresh activities, choose activity
        ACT: POST signup for Basketball Team with new email
        ASSERT: Verify student is in Basketball Team participants
        """
        # Arrange
        email = "new_student@mergington.edu"
        activity = "Basketball Team"

        # Act
        client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        response = client.get("/activities")

        # Assert
        activities = response.json()
        assert email in activities[activity]["participants"]
        assert len(activities[activity]["participants"]) == 1

    def test_signup_duplicate_registration_fails(self, client, fresh_activities):
        """
        Test that a student cannot sign up for the same activity twice.

        ARRANGE: Get fresh activities, signup student once
        ACT: Attempt same signup again
        ASSERT: Verify 400 status and "already signed up" error message
        """
        # Arrange
        email = "new_student@mergington.edu"
        activity = "Basketball Team"
        client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity_fails(self, client, fresh_activities):
        """
        Test that signing up for a non-existent activity returns 404.

        ARRANGE: (no setup)
        ACT: POST signup for "Fake Activity"
        ASSERT: Verify 404 status and "Activity not found" error
        """
        # Arrange
        email = "student@mergington.edu"
        activity = "Fake Activity"

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_response_message_format(self, client, fresh_activities):
        """
        Test that the signup response message has the correct format.

        ARRANGE: Get fresh activities
        ACT: POST signup and capture response
        ASSERT: Verify response contains email and activity name
        """
        # Arrange
        email = "student@mergington.edu"
        activity = "Swimming Club"

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        message = data["message"]
        assert email in message
        assert activity in message
        assert "Signed up" in message


class TestUnregisterEndpoint:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint."""

    def test_unregister_existing_participant_success(self, client, fresh_activities):
        """
        Test that an existing participant can be unregistered successfully.

        ARRANGE: Get fresh activities with participants (Chess Club)
        ACT: DELETE unregister for existing participant
        ASSERT: Verify 200 status and "Unregistered" message
        """
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert email in data["message"]
        assert activity in data["message"]

    def test_unregister_removes_from_participants(self, client, fresh_activities):
        """
        Test that unregistering removes the student from the participant list.

        ARRANGE: Get fresh activities, note Chess Club has michael@mergington.edu
        ACT: DELETE unregister michael from Chess Club
        ASSERT: Verify michael is no longer in Chess Club participants
        """
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"
        initial_response = client.get("/activities")
        initial_activities = initial_response.json()
        assert email in initial_activities[activity]["participants"]

        # Act
        client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        response = client.get("/activities")

        # Assert
        activities = response.json()
        assert email not in activities[activity]["participants"]
        assert len(activities[activity]["participants"]) == 1

    def test_unregister_nonexistent_activity_fails(self, client, fresh_activities):
        """
        Test that unregistering from a non-existent activity returns 404.

        ARRANGE: (no setup)
        ACT: DELETE unregister from "Fake Activity"
        ASSERT: Verify 404 status and "Activity not found" error
        """
        # Arrange
        email = "student@mergington.edu"
        activity = "Fake Activity"

        # Act
        response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_not_registered_student_fails(self, client, fresh_activities):
        """
        Test that unregistering a non-registered student returns 400.

        ARRANGE: Get fresh activities, choose empty activity (Basketball Team)
        ACT: DELETE unregister non-existent student from Basketball Team
        ASSERT: Verify 400 status and "not registered" error message
        """
        # Arrange
        email = "not_registered@mergington.edu"
        activity = "Basketball Team"

        # Act
        response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"].lower()

    def test_unregister_response_message_format(self, client, fresh_activities):
        """
        Test that the unregister response message has the correct format.

        ARRANGE: Get fresh activities
        ACT: DELETE unregister and capture response
        ASSERT: Verify response contains email and activity name
        """
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        message = data["message"]
        assert email in message
        assert activity in message
        assert "Unregistered" in message
