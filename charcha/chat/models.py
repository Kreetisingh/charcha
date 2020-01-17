from django.db import models
from charcha.team.models import Team, TeamMember


DIRECT_MESSAGE = 1
GROUP_DIRECT_MESSAGE = 2
PRIVATE_CHANNEL = 3
PUBLIC_CHANNEL = 4

# Will be added to TeamMember
def send_direct_message(self, recipient, text):
    channels = Channel.objects.raw('''SELECT c.id
        from channels c inner join channel_members me
        on c.id = me.channel_id and me.id = %s
        where c.team_id = %s and c.kind = %s
        and exists (select 1 from channel_members recipient
        where recipient.channel_id = c.id and recipient.member_id = %s)''',
        [self.id, self.team.id, DIRECT_MESSAGE, recipient.id])

    if channels:
        channel = channels[0]
    else:
        channel = _create_direct_message_channel(self.team, self, recipient)

    channel.post_message(self, text)

def _create_direct_message_channel(team, first, second):
    return _create_channel(team, '1-0-1', DIRECT_MESSAGE, members=[first, second])

def create_private_channel(self, channel_name, members=None):
    return _create_channel(self, channel_name, PRIVATE_CHANNEL, members)

def create_public_channel(self, channel_name, members=None):
    return _create_channel(self, channel_name, PUBLIC_CHANNEL, members)

def _create_channel(team, channel_name, kind, members=None):
    if not members:
        raise Exception("Cannot create channel without any members")

    channel = Channel(team=team, name=channel_name, kind=kind)
    channel.save()

    ChannelMember.objects.bulk_create(
        [ChannelMember(channel=channel, member=member) for member in members]
    )
    return channel

'''Basically we are having three database structure as messages ,channels , channel_members and performing
inner joins between channel_id attribute of messages table and id attribute of channels table whose
resultant table is inner joined with the channel_id attribute of channel_members table.
'''
def get_messages_since(self, last_message_id):
    return Message.objects.raw("""select m.* from messages m
    inner join channels c on m.channel_id = c.id
    inner join channel_members cm on c.id = cm.channel_id
    where cm.member_id = %s and m.id > %s""", [self.id, last_message_id])


# To remove circular dependency, we monkey patch member functions here
TeamMember.send_direct_message = send_direct_message
TeamMember.get_messages_since = get_messages_since
Team.create_private_channel = create_private_channel
Team.create_public_channel = create_public_channel

class Channel(models.Model):
    '''A channel is a chat room.

    There are 4 type of channels -
    1. 1-1 chat between two members
    2. group chat between multiple members
    3. private chat between multiple members
    4. public chat between multiple members

    The difference between 2 and 3 - group chat is a temporary channel,
    while a private chat is a named channel that is intended to be long lived

    Difference between public and private chat - any team member can join a public
    chat without an explict invite.
    '''
    class Meta:
        db_table = 'channels'

    name = models.CharField(max_length=100)
    team = models.ForeignKey(Team, on_delete=models.PROTECT)
    kind = models.IntegerField(choices = (
        (DIRECT_MESSAGE, 'Direct Message'),
        (GROUP_DIRECT_MESSAGE, 'Group Direct Message'),
        (PRIVATE_CHANNEL, 'Private Channel'),
        (PUBLIC_CHANNEL, 'Public Channel'),
    ))
    def post_message(self, author, text):
        'Post a text message on this channel'
        message = Message()
        message.channel = self
        message.text = text
        message.author = author
        message.save()

class ChannelMember(models.Model):
    '''Members of a channel
    '''
    class Meta:
        db_table = 'channel_members'

    channel = models.ForeignKey(Channel, on_delete=models.PROTECT, related_name="members")
    member = models.ForeignKey(TeamMember, on_delete=models.PROTECT)

class Message(models.Model):
    class Meta:
        db_table = 'messages'
    'A chat message'
    channel = models.ForeignKey(Channel, on_delete=models.PROTECT)
    text = models.TextField(max_length=8192)
    author = models.ForeignKey(TeamMember, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)
