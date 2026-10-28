import React from 'react';
import { motion } from 'framer-motion';
import { useTripStore } from '../store/tripStore';

export default function DisruptionRecoveryCard() {
  const { 
    activeDisruption, 
    impactAnalysis: impact, 
    recoveryCandidates,
    submitPreferences,
    selectCandidate
  } = useTripStore();

  if (!activeDisruption) return null;

  const handleOkay = () => {
    useTripStore.getState().shiftItinerary(activeDisruption.affected_stop_id, activeDisruption.delay_minutes || 15);
    useTripStore.getState().clearDisruption();
  };

  const handleStuck = () => {
    useTripStore.getState().setDisruptionStuck();
  };

  const handleSkip = () => {
    useTripStore.getState().skipToNextStop(activeDisruption.affected_stop_id);
    useTripStore.getState().clearDisruption();
  };

  const handleFindAlternative = () => {
    if (activeDisruption.type === 'WEATHER_DISRUPTION') {
      submitPreferences({ 
        categories: ['Indoor'], 
        disruption_type: activeDisruption.type,
        affected_stop_id: activeDisruption.affected_stop_id 
      });
    } else {
      submitPreferences({ 
        categories: ['Nearby', 'Outdoor', 'Indoor'], 
        disruption_type: activeDisruption.type,
        affected_stop_id: activeDisruption.affected_stop_id,
        delay_minutes: activeDisruption.delay_minutes || 15
      });
    }
  };

  const handleSelectAlternative = (candId) => {
    selectCandidate(candId);
    useTripStore.getState().clearDisruption();
  };

  return (
    <div className="fixed inset-x-0 bottom-6 z-[100] flex justify-center pointer-events-none px-4">
      <motion.div 
        initial={{opacity:0, y:50, scale:0.95}} 
        animate={{opacity:1, y:0, scale:1}} 
        className="w-full max-w-md p-6 bg-[#FAF9F6] rounded-2xl border border-orange-100 shadow-2xl pointer-events-auto max-h-[80vh] overflow-y-auto"
      >
        <div className="flex justify-between items-start mb-2">
          <h3 className="font-serif font-bold text-lg text-slate-900">
            {activeDisruption.type === 'WEATHER_DISRUPTION' ? '🌧 WEATHER DISRUPTION' : '⚠ DISRUPTION DETECTED'}
          </h3>
          <button 
            onClick={() => useTripStore.getState().clearDisruption()} 
            className="text-slate-400 hover:text-slate-600 text-xl leading-none"
          >
            &times;
          </button>
        </div>
        
        {!activeDisruption.showRecovery && !recoveryCandidates?.length && (
          <p className="text-sm text-slate-700 leading-relaxed font-medium">
            {activeDisruption.type === 'WEATHER_DISRUPTION' 
              ? 'Rain is expected around your upcoming outdoor activity.' 
              : `You're about ${activeDisruption.delay_minutes || 15} minutes behind.`}
          </p>
        )}

        {(activeDisruption.showRecovery || recoveryCandidates?.length > 0) && (
          <p className="text-sm text-slate-700 leading-relaxed font-medium mb-4">
            RECOVERY OPTIONS<br />
            <span className="font-normal text-slate-600">
              {activeDisruption.type === 'WEATHER_DISRUPTION'
                ? 'Weather is affecting your outdoor activity.'
                : 'You\'re behind schedule.'}
            </span>
          </p>
        )}

        {/* NORMAL DELAY PATH */}
        {activeDisruption.type !== 'WEATHER_DISRUPTION' && !activeDisruption.showRecovery && !recoveryCandidates?.length && (
          <div className="flex gap-3 mt-6">
            <button 
              onClick={handleOkay} 
              className="flex-1 py-3 bg-slate-100 text-slate-700 rounded-full text-xs font-bold uppercase tracking-widest hover:bg-slate-200 transition-colors shadow-sm"
            >
              I'm Okay
            </button>
            <button 
              onClick={handleStuck} 
              className="flex-1 py-3 bg-slate-900 text-white rounded-full text-xs font-bold uppercase tracking-widest hover:bg-slate-800 transition-colors shadow-md"
            >
              I'm Stuck
            </button>
          </div>
        )}

        {/* WEATHER DISRUPTION INITIAL */}
        {activeDisruption.type === 'WEATHER_DISRUPTION' && !activeDisruption.showRecovery && !recoveryCandidates?.length && (
          <div className="flex gap-3 mt-6">
            <button 
              onClick={handleOkay} 
              className="flex-1 py-3 bg-slate-100 text-slate-700 rounded-full text-xs font-bold uppercase tracking-widest hover:bg-slate-200 transition-colors shadow-sm"
            >
              I'm Okay
            </button>
            <button 
              onClick={handleStuck} 
              className="flex-1 py-3 bg-slate-900 text-white rounded-full text-xs font-bold uppercase tracking-widest hover:bg-slate-800 transition-colors shadow-md"
            >
              I'm Stuck
            </button>
          </div>
        )}

        {/* RECOVERY CHOICES */}
        {activeDisruption.showRecovery && !recoveryCandidates?.length && (
          <div className="flex flex-col gap-3 mt-4">
            <button
              onClick={handleFindAlternative}
              className="w-full py-3 bg-slate-900 text-white rounded-full text-xs font-bold uppercase tracking-widest hover:bg-slate-800 transition-all shadow-md"
            >
              Find Nearest Alternative
            </button>
            <button
              onClick={handleSkip}
              className="w-full py-3 bg-slate-100 text-slate-700 rounded-full text-xs font-bold uppercase tracking-widest hover:bg-slate-200 transition-all shadow-sm"
            >
              Skip To Next Location
            </button>
          </div>
        )}

        {/* RECOVERY CANDIDATES */}
        {recoveryCandidates && recoveryCandidates.length > 0 && (
          <div className="mt-6 border-t border-slate-200 pt-4">
            <h3 className="font-serif font-bold text-lg text-slate-900 mb-4">Suggested Alternatives</h3>
            <div className="space-y-4">
              {recoveryCandidates.map((cand, idx) => (
                <motion.div initial={{opacity:0, y:10}} animate={{opacity:1, y:0}} transition={{delay: idx*0.1}} key={cand.id} className="p-4 border border-slate-200 bg-white rounded-xl hover:border-slate-400 hover:shadow-md cursor-pointer transition-all group" onClick={() => selectCandidate(cand.id)}>
                  <h4 className="font-bold text-slate-800 group-hover:text-slate-900">{cand.name}</h4>
                  <p className="text-xs text-slate-500 mt-1 mb-2 font-medium tracking-wide">
                    {cand.distance_meters ? `${(cand.distance_meters / 1000).toFixed(1)} km · ` : ''}
                    {cand.travel_time_mins ? `~${cand.travel_time_mins} min` : cand.category}
                  </p>
                  <p className="text-sm text-slate-600 leading-relaxed">{cand.why_recommended}</p>
                  <div className="mt-3 text-right">
                    <span className="text-xs font-bold uppercase tracking-widest text-slate-900 bg-slate-100 px-4 py-2 rounded-full group-hover:bg-slate-200 transition-colors">Choose</span>
                  </div>
                </motion.div>
              ))}
            </div>
            <button
              onClick={handleSkip}
              className="w-full py-3 mt-4 bg-slate-100 text-slate-700 rounded-full text-xs font-bold uppercase tracking-widest hover:bg-slate-200 transition-all shadow-sm"
            >
              Skip This Stop
            </button>
          </div>
        )}
      </motion.div>
    </div>
  );
}
