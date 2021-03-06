pragma solidity ^0.4.25;
 
contract Betting {
 
    struct Bet {
        uint bet_id;
        uint creator_id;
        uint taker_id;
        uint atleast;
        uint stake;
        address sender;
        address taker;
    }
 
    Bet[] bets;

    function createBet(uint bet_id, uint creator_id, uint atleast, uint stake) {
        Bet memory bet = Bet(bet_id, creator_id, 0, atleast, stake, address(creator_id), address(0));
        bets.push(bet);
    }

    function takeBet(uint bet_id, uint taker_id) {
        for (uint i=0; i<bets.length; i++) {
            if (bets[i].bet_id == bet_id) {
                Bet storage bet = bets[i];
                bet.taker_id = taker_id;
                bet.taker = address(taker_id);            
            }
        }
    }

    function rewardWinner(uint bet_id, uint temp) returns (uint) {
        for (uint i=0; i<bets.length; i++) {
            if (bets[i].bet_id == bet_id) {
                if (temp >= bet.atleast) {
                    Bet storage bet = bets[i];
                    bet.sender.transfer(bet.stake);
                    return bet.creator_id;
                } else {
                    bet.taker.transfer(bet.stake);
                    return bet.taker_id;
                }
            }
        }
        return 0;
    }

}