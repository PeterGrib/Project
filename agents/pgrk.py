import random
import pickle
import os
import numpy as np
import copy


class Agent(object):
    def __init__(self, agent_number, params={}):
        self.this_agent_number = agent_number  # index for this agent
        self.opponent_number = 1 - agent_number  # index for opponent
        self.n_items = params["n_items"]

        # Unpickle the trained model
        # Complications: pickle should work with any machine learning models
        # However, this does not work with custom defined classes, due to the way pickle operates
        # TODO you can replace this with your own model
        self.filename = 'agents/pgrk_files/trained_model'
        self.trained_model = pickle.load(open(self.filename, 'rb'))

        self.item0_embedding = [0.12277592821655194,
                                0.8848570813366212,
                                -0.7556286732829098,
                                0.9490172960627021,
                                0.6702740700696965,
                                -1.209413756554651,
                                -0.2610547783766926,
                                0.4517198188232259,
                                -0.8265020776064129,
                                0.2700059980528833]
        self.item1_embedding = [0.659227815368504,
                                -0.14133051653919068,
                                0.08777977176734512,
                                -1.0989246196354665,
                                1.2703206502381699,
                                2.4131725160613238,
                                -0.7559907972194396,
                                -0.9461158749689281,
                                0.3349207822918375,
                                -0.08573474488666911]

        # self.item0avg = -1.2359906243308039
        # self.item1avg = -1.939401864728488

        self.avg_user =   [-0.290928,
                            -0.022804,
                            -0.020025,
                            -0.016612,
                            -1.484994,
                            0.018343,
                            -0.005524,
                            -0.076671,
                            0.102322,
                            0.000550]

        self.losing_streak = 0
        self.winning_streak = 0

        self.discount_lower = .9
        self.discount_upper = 1

        self.floorer = False


    def _process_last_sale(self, last_sale, profit_each_team):
        # print("last_sale: ", last_sale)
        # print("profit_each_team: ", profit_each_team)
        my_current_profit = profit_each_team[self.this_agent_number]
        opponent_current_profit = profit_each_team[self.opponent_number]

        my_last_prices = last_sale[2][self.this_agent_number]
        opponent_last_prices = last_sale[2][self.opponent_number]

        did_customer_buy_from_me = last_sale[1] == self.this_agent_number
        did_customer_buy_from_opponent = last_sale[1] == self.opponent_number

        which_item_customer_bought = last_sale[0]

        if did_customer_buy_from_me:
            self.winning_streak += 1
            self.losing_streak = 0
            self.discount_lower += (self.winning_streak)*.05
            self.discount_upper += (self.winning_streak)*.05
        else:
            self.winning_streak = 0
            self.losing_streak += 1
            self.discount_lower -= (self.losing_streak)*.1
            self.discount_upper -= (self.losing_streak)*.1


        if opponent_last_prices[0] <= 0 or opponent_last_prices[1] <= 0:
            price_0_diff = 1
            price_1_diff = 1
        else:
            price_0_diff = my_last_prices[0]/opponent_last_prices[0]
            price_1_diff = my_last_prices[1]/opponent_last_prices[1]
        #
        if (price_0_diff < .5 and my_last_prices[0] > .10) or (price_1_diff < .5 and my_last_prices[1] >.2):
            self.discount_upper = 1
            self.discount_lower = .9
            self.winning_streak = 0
            self.losing_streak = 0

        if opponent_last_prices[0] < 1 and opponent_last_prices[1] < 1:
            self.floorer = True
        else:
            self.floorer = False

        # print("My current profit: ", my_current_profit)
        # print("Opponent current profit: ", opponent_current_profit)
        # print("My last prices: ", my_last_prices)
        # print("Opponent last prices: ", opponent_last_prices)
        # print("Did customer buy from me: ", did_customer_buy_from_me)
        # print("Did customer buy from opponent: ",
        #       did_customer_buy_from_opponent)
        # print("Which item customer bought: ", which_item_customer_bought)

        # TODO - add your code here to potentially update your pricing strategy based on what happened in the last round
        pass

    # Given an observation which is #info for new buyer, information for last iteration, and current profit from each time
    # Covariates of the current buyer, and potentially embedding. Embedding may be None
    # Data from last iteration (which item customer purchased, who purchased from, prices for each agent for each item (2x2, where rows are agents and columns are items)))
    # Returns an action: a list of length n_items=2, indicating prices this agent is posting for each item.
    def action(self, obs):

        new_buyer_covariates, new_buyer_embedding, last_sale, profit_each_team = obs
        self._process_last_sale(last_sale, profit_each_team)


        cust_data = new_buyer_covariates.tolist()


        if type(new_buyer_embedding) != list:
            cust_data.append(np.dot(self.avg_user, self.item0_embedding))
            cust_data.append(np.dot(self.avg_user, self.item1_embedding))

        else:
            cust_data.append(np.dot(new_buyer_embedding, self.item0_embedding))
            cust_data.append(np.dot(new_buyer_embedding, self.item1_embedding))



        def set_prices(input):

            item0_prices = np.arange(0,2.22, .75)
            item1_prices = np.arange(0,4,.75)

            prices = []
            revenues = []


            max_rev = 0
            max_1 = 0
            max_2 = 0
            for j in item0_prices:
                for k in item1_prices:
                    # print(k)
                # test_array = []
                # print(test_array)
                # for element in cust_data:
                #     test_array.append(element)
                    test_array = copy.deepcopy(input)
                    test_array.insert(0, j)
                    test_array.insert(1, k)
                    # print("tarray", test_array)
                    # print("input",input)
                    test_array = np.asarray(test_array)
                    # print("tarray_np", test_array)
                    proba = self.trained_model.predict_proba(test_array.reshape(1,-1))

                    expect_rev = test_array[0]*proba[0][1]+test_array[1]*proba[0][2]
                    # test_array = []
                    # test_array = test_array.pop(0)
                    # print(test_array)
                    if expect_rev>max_rev:
                        max_rev = expect_rev
                        max_1 = j
                        max_2 = k
            prices.append([max_1, max_2])
            revenues.append(max_rev)



            for i in range(len(prices)):
                for j in np.arange(prices[i][0]-.5, prices[i][0]+.5, .25):
                    for k in np.arange(prices[i][1]-.5, prices[i][1]+.5, .25):
                        test_array = copy.deepcopy(input)
                        test_array.insert(0, j)
                        test_array.insert(1, k)
                        # print(test_array)
                        test_array = np.asarray(test_array)
                        proba = self.trained_model.predict_proba(test_array.reshape(1,-1))
                        expect_rev = test_array[0]*proba[0][1]+test_array[1]*proba[0][2]

                        if expect_rev > revenues[i]:
                            revenues[i] = expect_rev
                            prices[i][0] = j
                            prices[i][1] = k

            for i in range(len(prices)):
                for j in np.arange(prices[i][0]-.25, prices[i][0]+.25, .1):
                    for k in np.arange(prices[i][1]-.25, prices[i][1]+.25, .1):
                        test_array = copy.deepcopy(input)
                        test_array.insert(0, j)
                        test_array.insert(1, k)
                        test_array = np.asarray(test_array)
                        proba = self.trained_model.predict_proba(test_array.reshape(1,-1))
                        expect_rev = test_array[0]*proba[0][1]+test_array[1]*proba[0][2]

                        if expect_rev > revenues[i]:
                            revenues[i] = expect_rev
                            prices[i][0] = j
                            prices[i][1] = k

            for i in range(len(prices)):
                for j in np.arange(prices[i][0]-.1, prices[i][0]+.1, .05):
                    for k in np.arange(prices[i][1]-.1, prices[i][1]+.1, .05):
                        test_array = copy.deepcopy(input)
                        test_array.insert(0, j)
                        test_array.insert(1, k)
                        test_array = np.asarray(test_array)
                        proba = self.trained_model.predict_proba(test_array.reshape(1,-1))
                        expect_rev = test_array[0]*proba[0][1]+test_array[1]*proba[0][2]

                        if expect_rev > revenues[i]:
                            revenues[i] = expect_rev
                            prices[i][0] = j
                            prices[i][1] = k

            for i in range(len(prices)):
                for j in np.arange(prices[i][0]-.05, prices[i][0]+.05, .01):
                    for k in np.arange(prices[i][1]-.05, prices[i][1]+.05, .01):
                        test_array = copy.deepcopy(input)
                        test_array.insert(0, j)
                        test_array.insert(1, k)
                        test_array = np.asarray(test_array)
                        proba = self.trained_model.predict_proba(test_array.reshape(1,-1))
                        expect_rev = test_array[0]*proba[0][1]+test_array[1]*proba[0][2]

                        if expect_rev > revenues[i]:
                            revenues[i] = expect_rev
                            prices[i][0] = j
                            prices[i][1] = k

            for i in range(len(prices)):
                for j in np.arange(prices[i][0]-.01, prices[i][0]+.01, .005):
                    for k in np.arange(prices[i][1]-.01, prices[i][1]+.01, .005):
                        test_array = copy.deepcopy(input)
                        test_array.insert(0, j)
                        test_array.insert(1, k)
                        test_array = np.asarray(test_array)
                        proba = self.trained_model.predict_proba(test_array.reshape(1,-1))
                        expect_rev = test_array[0]*proba[0][1]+test_array[1]*proba[0][2]

                        if expect_rev > revenues[i]:
                            revenues[i] = expect_rev
                            prices[i][0] = j
                            prices[i][1] = k

            no_strat_prices = prices[0]
            print(no_strat_prices)
            return no_strat_prices

        no_strat_prices = set_prices(cust_data)

        discount_factor = random.uniform(self.discount_lower, self.discount_upper)

        no_strat_prices[0] *= discount_factor
        no_strat_prices[1] *= discount_factor

        output = []
        output.append(max(0, no_strat_prices[0]))
        output.append(max(0, no_strat_prices[1]))
        if self.floorer:
            output = []
            output.append(.15)
            output.append(.15)

        return output
        # TODO Currently this output is just a deterministic 2-d array, but the students are expected to use the buyer covariates to make a better prediction
        # and to use the history of prices from each team in order to create prices for each item.
