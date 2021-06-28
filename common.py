import uuid
import base64
import codecs


def generate_random_slug_code(length=32):
    """
    generates random code of given length
    """
    return base64.urlsafe_b64encode(
        codecs.encode(uuid.uuid4().bytes, "base64").rstrip()
    ).decode()[:length]


class UserAgentParser:
    from user_agents import parse  # // VERSION: 2.2.0
    from collections import namedtuple

    UA3Layers = namedtuple(
        typename="UA3Layers",
        field_names=[
            "str_browser_name",
            "str_operating_system_name",
            "str_hardware_type_name",
        ],
    )

    class HardwareType:
        SERVER = "Server"
        TABLET = "Tablet"
        PHONE = "Phone"
        COMPUTER = "Computer"
        OTHER = "Other"

    def get_3layers(self, str_user_agent):
        user_agent = self.__class__.parse(str_user_agent)
        return self.__class__.UA3Layers(
            self.get_browser_name(user_agent),
            self.get_operating_system_name(user_agent),
            self.get_hardware_type(user_agent),
        )

    def get_browser_name(self, user_agent):
        """
        Return: ['Chrome', 'Firefox', 'Opera', 'IE', 'Edge', 'Safari', ...]
        변환로직:
            'IE Mobile' >>> 'IE'
            'Mobile Safari' >>> 'Safari'
        """
        str_browser_name = user_agent.browser.family
        str_browser_name = str_browser_name.replace("Mobile", "").strip()
        return str_browser_name

    def get_operating_system_name(self, user_agent):
        """
        Return: ['Windows','Linux','Mac OS X','iOS','Android','OpenBSD','BlackBerry OS','Chrome OS',...]
        """
        str_operating_system_name = user_agent.os.family
        return str_operating_system_name

    def get_hardware_type(self, user_agent):
        if user_agent.is_bot:
            str_hardware_type_name = self.__class__.HardwareType.SERVER
        elif user_agent.is_tablet:
            str_hardware_type_name = self.__class__.HardwareType.TABLET
        elif user_agent.is_mobile:
            str_hardware_type_name = self.__class__.HardwareType.PHONE
        elif user_agent.is_pc:
            str_hardware_type_name = self.__class__.HardwareType.COMPUTER
        else:
            str_hardware_type_name = self.__class__.HardwareType.OTHER
        return str_hardware_type_name
