from django.test import TestCase
from charcha.discussions.models import User
from charcha.team.models import Team, TeamMember, ADMIN, MEMBER

from .models import Channel, Message

class DiscussionTests(TestCase):
    def setUp(self):
        self._create_team()

    def _create_team(self):
        team = Team(name="Trial team")
        team.save()
        self.team = team

        Ankita = User.objects.create_user(
            username="Ankita", password="top_secret")
        Ansh = User.objects.create_user(
            username="Ansh", password="top_secret")
        Smriti = User.objects.create_user(
            username="Smriti", password="top_secret")

        self.Ankita = TeamMember(team=team, user=Ankita, role=ADMIN)
        self.Ankita.save()
        self.Ansh = TeamMember(team=team, user=Ansh, role=MEMBER)
        self.Ansh.save()
        self.Smriti = TeamMember(team=team, user=Smriti, role=MEMBER)
        self.Smriti.save()

    def test_private_message(self):
        Ankita, Ansh, Smriti = self.Ankita, self.Ansh, self.Smriti

        self.assertTrue(not Ankita.get_messages_since(0))
        self.assertTrue(not Ansh.get_messages_since(0))

        self.Ankita.send_direct_message(self.Ansh, "Hey Ansh!")
        self.Ankita.send_direct_message(self.Ansh, "How are you today?")

        self.assertEquals(len(Ankita.get_messages_since(0)), 2)
        self.assertEquals(len(Ansh.get_messages_since(0)), 2)
        self.assertEquals(len(Smriti.get_messages_since(0)), 0)

        self.Ansh.send_direct_message(self.Ankita, "I am doing good. How about you?")

        self.assertEquals(len(Ankita.get_messages_since(0)), 3)
        self.assertEquals(len(Ankita.get_messages_since(2)), 1)
        self.assertEquals(len(Ansh.get_messages_since(2)), 1)
        self.assertEquals(len(Smriti.get_messages_since(0)), 0)
