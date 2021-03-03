import aiohttp
import discord
from discord.ext import commands

from bot.constants import Tokens

UnClient_id = Tokens.unsplash_key


class EarthPhotos(commands.Cog):
    """This cog contains the command for earth photos."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.current_channel = None

    @commands.command(aliases=["earth"])
    async def earth_photos(self, ctx: commands.Context) -> None:
        """Returns a random photo of earth, sourced from Unsplash."""
        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        'https://api.unsplash.com/photos/random?query=earth&client_id=' + UnClient_id) as r:
                    jsondata = await r.json()
                    linksdata = jsondata.get("urls")
                    embedlink = linksdata.get("full")
                    downloadlinksdata = jsondata.get("links")
                    userdata = jsondata.get("user")
                    username = userdata.get("name")
                    userlinks = userdata.get("links")
                    profile = userlinks.get("html")
                async with session.get(
                        downloadlinksdata.get("download_location") + "?client_id=" + UnClient_id) as er:
                    er.status
                embed = discord.Embed(
                    title="Earth Photo",
                    description="A photo of earth from Unsplash.",
                    color=0x66ff00)
                embed.set_image(url=embedlink)
                embed.add_field(title="Author", value="Made by [" + username + "](" + profile + ") on Unsplash.")
            await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Load the Earth Photos cog."""
    bot.add_cog(EarthPhotos(bot))
