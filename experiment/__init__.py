from otree.api import *
import random
import math


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'experiment'
    NUM_ROUNDS = 1
    society_size = 16
    num_hires = 4
    mean_productivity = 100
    variance_productivity = 10000
    variance_signal = 10000
    tokens_to_dollars = 0.01
    PLAYERS_PER_GROUP = None
    CORRECT_ANSWERS = [3, 3, 1, 3, 2, 2]
    CORRECT_ANSWERS2 = [2, 3, 3]
    ERROR_MESSAGES = [
        'Your answer to question 1 is wrong. Your society consists of 16 people (including you!).',
        'Your answer to question 2 is wrong. Everyone draws a productivity value from the same urn where the average ball number is 100.',
        'Your answer to question 3 is wrong. You can draw a negative value (the probability of this happening is 15.9%).',
        'Your answer to question 4 is wrong. Signals are made by adding the numbers drawn from the productivity and noise urns.',
        'Your answer to question 5 is wrong. 4 individuals will be hired.',
        'Your answer to question 6 is wrong. The noise urn contains negative valued numbers so your signal can be less than your productivity value.'
    ]
    ERROR_MESSAGES2 = [
        'Your answer to question 7 is wrong. Robot A first subtracts 50 from each signal of Green applicants.',
        'Your answer to question 8 is wrong. Robot B uses signals, colors and its prediction of the distribution of productivity values among applicants from each group.',
        'Your answer to question 9 is wrong. You do not know which robot will be used.'
    ]


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    #Fundamentals
    consent = models.IntegerField(initial=0)
    website = models.StringField(blank=True)  # Honeypot - should be empty
    math_answer = models.StringField()  # Human verification math question
    completion_time = models.IntegerField()  # Time taken to complete page
    interaction_data = models.StringField()  # JSON string of mouse/keyboard data
    slider = models.IntegerField(blank=True)
    # Existing fields...
    human_check = models.StringField(blank=True)  # You can remove this old one
    color = models.IntegerField(
        choices = [
        [1, 'Green'],
        [2, 'Purple']
        ]
    )
    productivity_value = models.IntegerField()
    signal_value = models.FloatField()

    #Decision info
    apply = models.BooleanField()
    #apply_bonus_tokens = models.IntegerField()
    #guesses_green = models.IntegerField()
    #guesses_purple = models.FloatField()
    #guess_robot_a = models.IntegerField(min=0, max=200)
    #guess_robot_b = models.IntegerField()
    #confidence = models.StringField()

    quiz_q1 = models.IntegerField(choices=[[1, '8'], [2, '10'], [3, '16'], [4, '20']], label='Number in society', widget=widgets.RadioSelect)
    incorrect1 = models.IntegerField(initial=0)
    quiz_q2 = models.IntegerField(choices=[[1, '50'], [2, '90'], [3, '100'], [4, '125']],
                                  label='Expected avg productivity', widget=widgets.RadioSelect)
    incorrect2 = models.IntegerField(initial=0)
    quiz_q3 = models.IntegerField(choices=[[1, 'TRUE'], [2, 'FALSE']], label='Negative productivity possible?', widget=widgets.RadioSelect)
    incorrect3 = models.IntegerField(initial=0)
    quiz_q4 = models.IntegerField(choices=[[1, 'Signals are drawn from an urn with mean 0'], [2, 'Signals are equal to productivity values plus 100'], [3, 'Signals are equal to productivity values plus a draw from the noise urn']], label='Same signal urn?', widget=widgets.RadioSelect)
    incorrect4 = models.IntegerField(initial=0)
    quiz_q5 = models.IntegerField(choices=[[1, '2'], [2, '4'], [3, '5'], [4, '8']], label='Number hired', widget=widgets.RadioSelect)
    incorrect5 = models.IntegerField(initial=0)
    quiz_q6 = models.IntegerField(choices=[[1, 'TRUE'], [2, 'FALSE']], label='Negative signal', widget=widgets.RadioSelect)
    incorrect6 = models.IntegerField(initial=0)

    quiz_q7 = models.IntegerField(choices=[[1, 'Adds 50 points'], [2, 'Subtracts 50 points'],
                                           [3, 'Nothing special'], [4, 'Uses sophisticated analysis']], label='Robot A', widget=widgets.RadioSelect)
    quiz_q8 = models.IntegerField(choices=[[1, 'Only each applicant\'s signal'], [2, 'Only each applicant\'s group colour'],
                                           [3, 'Group productivity predictions combined with each applicant\'s signal and colour'],
                                           [4, 'Random selection from each group']], label='Robot B', widget=widgets.RadioSelect)
    quiz_q9 = models.IntegerField(choices=[[1, 'Know which robot will be used for your society'], [2, 'Can choose which robot to use'],
                                           [3, 'Do not know which robot will be used'],
                                           [4, 'Will use both robots for different decisions']], label='Which robot', widget=widgets.RadioSelect)
    bot = models.IntegerField(initial=0)

# PAGES
class Welcome(Page):
    form_model = 'player'
    form_fields = ['consent']

class Intro(Page):
    form_model = 'player'
    form_fields = [ 'website',          # Honeypot field
        'math_answer',      # Math verification
        'completion_time',  # Hidden time tracking
        'interaction_data'  # Hidden interaction tracking
    ]

    @staticmethod
    def before_next_page(player, timeout_happened):
        import json

        def is_likely_bot(player_data):
            # Check honeypot
            if player_data.get('website', '').strip():  # Should be empty
                return True

            # Check math answer
            if player_data.get('math_answer') != '22':
                return True

            # Check completion time (too fast = bot)
            completion_time = int(player_data.get('completion_time', 0))
            if completion_time < 1000:  # Less than 5 seconds
                return True

            # Check interaction data
            try:
                interactions = json.loads(player_data.get('interaction_data', '{}'))
                if interactions.get('mouse', 0) < 5:  # No mouse movement
                    return True
            except (json.JSONDecodeError, TypeError):
                return True  # Invalid interaction data = bot

            return False

        # Prepare player data for bot detection
        player_data = {
            'website': player.website,
            'math_answer': player.math_answer,
            'completion_time': player.completion_time,
            'interaction_data': player.interaction_data
        }

        # Run bot detection and flag player if detected
        if is_likely_bot(player_data):
            player.bot = 1
        else:
            player.bot = 0

class Overview(Page):

    @staticmethod
    def before_next_page(player, timeout_happened):
        player.color = random.randint(1,2)


class Color(Page):

    @staticmethod
    def vars_for_template(player):
        if player.color == 1:
            color = 'GREEN'
        else:
            color = 'PURPLE'

        return {
            'color': color
        }

    @staticmethod
    def before_next_page(player, timeout_happened):
        player.productivity_value = math.ceil(random.gauss(100,100))

class Productivity(Page):
    form_model = 'player'
    form_fields = ['slider']

class Signal(Page):

    @staticmethod
    def vars_for_template(player):
        return {
            'slider_min': player.productivity_value - 200,
            'prod_min': player.productivity_value - 100,
            'prod_max': player.productivity_value + 100,
            'slider_max': player.productivity_value + 200,
            'user_productivity': player.productivity_value
        }

class Quiz1(Page):
    form_model = 'player'
    form_fields = [
        'quiz_q1',
        'quiz_q2',
        'quiz_q3',
        'quiz_q4',
        'quiz_q5',
        'quiz_q6'
                   ]

    @staticmethod
    def vars_for_template(self):
        return {
            'correct_answers': C.CORRECT_ANSWERS,
            'error_messages': C.ERROR_MESSAGES,
        }

    @staticmethod
    def error_message(player, values):
        if values['quiz_q1'] != C.CORRECT_ANSWERS[0]:
            player.incorrect1 = 1
            return C.ERROR_MESSAGES
        elif values['quiz_q2'] != C.CORRECT_ANSWERS[1]:
            player.incorrect2 = 1
            return C.ERROR_MESSAGES
        elif values['quiz_q3'] != C.CORRECT_ANSWERS[2]:
            player.incorrect3 = 1
            return C.ERROR_MESSAGES
        elif values['quiz_q4'] != C.CORRECT_ANSWERS[3]:
            player.incorrect4 = 1
            return C.ERROR_MESSAGES
        elif values['quiz_q5'] != C.CORRECT_ANSWERS[4]:
            player.incorrect5 = 1
            return C.ERROR_MESSAGES
        elif values['quiz_q6'] != C.CORRECT_ANSWERS[5]:
            player.incorrect6 = 1
            return C.ERROR_MESSAGES

class Employer(Page):
    pass

class Quiz2(Page):
    form_model = 'player'
    form_fields = [
        'quiz_q7',
        'quiz_q8',
        'quiz_q9'
    ]

    @staticmethod
    def vars_for_template(self):
        return {
            'correct_answers2': C.CORRECT_ANSWERS2,
            'error_messages2': C.ERROR_MESSAGES2,
        }

    @staticmethod
    def error_message(player, values):
        if values['quiz_q7'] != C.CORRECT_ANSWERS2[0]:
            player.incorrect7 = 1
            return C.ERROR_MESSAGES
        elif values['quiz_q8'] != C.CORRECT_ANSWERS2[1]:
            player.incorrect8 = 1
            return C.ERROR_MESSAGES
        elif values['quiz_q9'] != C.CORRECT_ANSWERS2[2]:
            player.incorrect9 = 1
            return C.ERROR_MESSAGES2

class Decision1(Page):
    form_model = 'player'
    form_fields = [
        'apply'
    ]

    @staticmethod
    def vars_for_template(player):
        if player.color == 1:
            color = 'GREEN'
        else:
            color = 'PURPLE'

        return {
            'color': color
        }

class Results(Page):

    @staticmethod
    def vars_for_template(player):
        dollar_value = player.productivity_value / 100
        dollar_str = f"{dollar_value:.2f}"

        return {
            'dollar_value': dollar_str,
        }

class Redirect(Page):
    @staticmethod
    def js_vars(player):
        return dict(
            completionlinkfull=
            player.subsession.session.config['completionlinkfull']
        )


page_sequence = [
    Welcome,
    Intro,
    Overview,
    Color,
    Productivity,
    Signal,
    #Quiz1,
    Employer,
    Quiz2,
    Decision1,
    Results,
    Redirect
    ]
