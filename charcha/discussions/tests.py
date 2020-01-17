from django.test import TestCase
from django.contrib.auth.models import AnonymousUser
from .models import Post, Vote, Comment, User

class DiscussionTests(TestCase):
    def setUp(self):
        self._create_users()

    def _create_users(self):
        self.Ankita = User.objects.create_user(
            username="Ankita", password="top_secret")
        self.Ansh = User.objects.create_user(
            username="Ansh", password="top_secret")
        self.Smriti = User.objects.create_user(
            username="Smriti", password="top_secret")
        self.anamika = AnonymousUser()

    def new_discussion(self, user, title):
        post = Post(title=title,
            text="Does not matter",
            author=user)
        post.save()
        return post

    def test_I_cant_vote_for_me(self):
        post = self.new_discussion(self.Ankita, "Ankita's Biography")
        self.assertEquals(post.upvotes, 0)
        post.upvote(self.Ankita)
        post = Post.objects.get(pk=post.id)
        self.assertEquals(post.upvotes, 0)

    def test_double_voting(self):
        post = self.new_discussion(self.Ankita, "Ankita's Biography")
        self.assertEquals(post.upvotes, 0)
        post.upvote(self.Ansh)
        post = Post.objects.get(pk=post.id)
        self.assertEquals(post.upvotes, 1)
        post.upvote(self.Ansh)
        post = Post.objects.get(pk=post.id)
        self.assertEquals(post.upvotes, 1)

    def test_voting_on_home_page(self):
        # Ankita starts a discussion
        post = self.new_discussion(self.Ankita, "Ankita's Biography")

        # Then Anamika views home page
        posts = Post.objects.recent_posts_with_my_votes()
        self.assertEquals(len(posts), 1)
        post = posts.first()
        self.assertEquals(post.upvotes, 0)
        self.assertEquals(post.downvotes, 0)

        # Ansh upvotes the post
        post.upvote(self.Ansh)

        # Home page as seen by Ansh
        post = Post.objects.recent_posts_with_my_votes(self.Ansh).first()
        self.assertTrue(post.is_upvoted)
        self.assertFalse(post.is_downvoted)
        self.assertEquals(post.upvotes, 1)
        self.assertEquals(post.downvotes, 0)

        # Smriti downvotes
        post.downvote(self.Smriti)

        # Home page as seen by Smriti
        post = Post.objects.recent_posts_with_my_votes(self.Smriti).first()
        self.assertFalse(post.is_upvoted)
        self.assertTrue(post.is_downvoted)
        self.assertEquals(post.upvotes, 1)
        self.assertEquals(post.downvotes, 1)

        # Ansh undo's his vote
        post.undo_vote(self.Ansh)

        # Home page as seen by Ansh
        post = Post.objects.recent_posts_with_my_votes(self.Ansh).first()
        self.assertFalse(post.is_upvoted)
        self.assertFalse(post.is_downvoted)
        self.assertEquals(post.upvotes, 0)
        self.assertEquals(post.downvotes, 1)

    def test_comments_ordering(self):
        _c1 = "See my Biography!"
        _c2 = "Dude, this is terrible!"
        _c3 = "Why write your biography when you haven't achieved a thing!"
        _c4 = "Seriously, that's all you have to say?"

        post = self.new_discussion(self.Ankita, "Ankita's Biography")
        self.assertEquals(post.num_comments, 0)

        Ankitas_comment = post.add_comment(_c1, self.Ankita)
        Anshs_comment = Ankitas_comment.reply(_c2, self.Ansh)
        Smritis_comment = Ankitas_comment.reply(_c3, self.Smriti)
        Ankitas_response = Anshs_comment.reply(_c4, self.Ankita)

        comments = [c.text for c in
                    Comment.objects.best_ones_first(post.id, self.Ankita.id)]

        self.assertEquals(comments, [_c1, _c2, _c4, _c3])

        # check if num_comments in post object is updated
        post = Post.objects.get(pk=post.id)
        self.assertEquals(post.num_comments, 4)
