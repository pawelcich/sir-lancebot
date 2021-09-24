import asyncio
from contextlib import suppress
from functools import partial
from pathlib import Path

import discord
import yaml
from discord.ext import commands

from bot.bot import Bot
from bot.constants import MODERATION_ROLES, WHITELISTED_CHANNELS
from bot.utils.decorators import whitelist_override
from bot.utils.randomization import RandomCycle

SUGGESTION_FORM = "https://forms.gle/zw6kkJqv8U43Nfjg9"

with Path("bot/resources/utilities/starter.yaml").open("r", encoding="utf8") as f:
    STARTERS = yaml.load(f, Loader=yaml.FullLoader)

with Path("bot/resources/utilities/py_topics.yaml").open("r", encoding="utf8") as f:
    # First ID is #python-general and the rest are top to bottom categories of Topical Chat/Help.
    PY_TOPICS = yaml.load(f, Loader=yaml.FullLoader)

    # Removing `None` from lists of topics, if not a list, it is changed to an empty one.
    PY_TOPICS = {k: [i for i in v if i] if isinstance(v, list) else [] for k, v in PY_TOPICS.items()}

    # All the allowed channels that the ".topic" command is allowed to be executed in.
    ALL_ALLOWED_CHANNELS = list(PY_TOPICS.keys()) + list(WHITELISTED_CHANNELS)

# Putting all topics into one dictionary and shuffling lists to reduce same-topic repetitions.
ALL_TOPICS = {"default": STARTERS, **PY_TOPICS}
TOPICS = {
    channel: RandomCycle(topics or ["No topics found for this channel."])
    for channel, topics in ALL_TOPICS.items()
}


class ConvoStarters(commands.Cog):
    """General conversation topics."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @staticmethod
    def _build_topic_embed(channel_id: int) -> discord.Embed:
        """
        Build an embed containing a conversation topic.

        If in a Python channel, a python-related topic will be given.
        Otherwise, a random conversation topic will be received by the user.
        """
        # No matter what, the form will be shown.
        embed = discord.Embed(
            description=f"Suggest more topics [here]({SUGGESTION_FORM})!",
            color=discord.Color.blurple()
        )

        try:
            channel_topics = TOPICS[channel_id]
        except KeyError:
            # Channel doesn't have any topics.
            embed.title = f"**{next(TOPICS['default'])}**"
        else:
            embed.title = f"**{next(channel_topics)}**"
        return embed

    def _predicate(self, message: discord.Message, reaction: discord.Reaction, user: discord.User) -> bool:
        right_reaction = (
            user != self.bot.user
            and reaction.message.id == message.id
            and str(reaction.emoji) == "🔄"
        )
        if not right_reaction:
            return False

        is_moderator = any(role.id in MODERATION_ROLES for role in getattr(user, "roles", []))
        if is_moderator or user.id == message.author.id:
            return True

        return False

    async def _listen_for_refresh(self, message: discord.Message) -> None:
        await message.add_reaction("🔄")
        while True:
            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add",
                    check=partial(self._predicate, message),
                    timeout=60.0
                )
            except asyncio.TimeoutError:
                with suppress(discord.NotFound):
                    await message.clear_reaction("🔄")
            else:
                await message.edit(embed=self._build_topic_embed(message.channel.id))

    @commands.command()
    @commands.cooldown(1, 300, commands.BucketType.channel)
    @whitelist_override(channels=ALL_ALLOWED_CHANNELS)
    async def topic(self, ctx: commands.Context) -> None:
        """
        Responds with a random topic to start a conversation.

        Allows the refresh of a topic by pressing an emoji.
        """
        message = await ctx.send(embed=self._build_topic_embed(ctx.channel.id))
        self.bot.loop.create_task(self._listen_for_refresh(message))


def setup(bot: Bot) -> None:
    """Load the ConvoStarters cog."""
    bot.add_cog(ConvoStarters(bot))
