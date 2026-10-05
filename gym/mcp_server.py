from mcp.server.fastmcp import FastMCP
from gym.db import gym

mcp = FastMCP('Gym Manager')
for name in ('add_member','search_members','create_plan','list_plans','activate_membership','record_payment','memberships','expiring_memberships'):
    method = getattr(gym, name)
    mcp.add_tool(method, name=name, description={
        'add_member':'Register a gym member with name and phone.',
        'search_members':'Search members by name or phone; at most 100 results.',
        'create_plan':'Create a plan with a duration in days and price in INR.',
        'list_plans':'List membership plans.',
        'activate_membership':'Create a membership from a plan; ISO start_date, inclusive end date. Does not record payment.',
        'record_payment':'Record an offline INR payment using a unique reference; does not charge money.',
        'memberships':'List a member’s memberships, agreed fees and total payments.',
        'expiring_memberships':'List memberships ending from today through the next specified number of days.'
    }[name])

if __name__ == '__main__':
    mcp.run(transport='stdio')
