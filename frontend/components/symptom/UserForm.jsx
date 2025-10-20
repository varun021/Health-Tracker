import React, { useState, useEffect } from 'react';
import { create } from 'zustand';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Loader2, Activity, AlertCircle, CheckCircle2, User, Calendar, Stethoscope, TrendingUp, Heart, Utensils, Dumbbell } from 'lucide-react';
import { userApi } from "@/lib/api-services";
import useAuthStore from '@/stores/useAuthStore';
import { useRouter } from 'next/navigation';

// Zustand store
const useStore = create((set) => ({
  symptoms: [],
  prediction: null,
  loading: false,
  error: null,
  setSymptoms: (symptoms) => set({ symptoms }),
  setPrediction: (prediction) => set({ prediction }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  reset: () => set({ prediction: null, error: null })
}));

export default function MedicalPredictionApp() {
  const { user, isAuthenticated, isLoading } = useAuthStore();
  const router = useRouter();

  const [formData, setFormData] = useState({
    name: '',
    age: '',
    gender: '',
    height: '',
    weight: '',
    occupation: '',
    selectedSymptoms: {},
    existing_diseases: [],
    allergies: '',
    medications: '',
    family_history: '',
    lifestyle: {
      smoking: false,
      alcohol: false,
      diet: '',
      sleep_hours: '',
      exercise_frequency: '',
      stress_level: ''
    },
    travel_history: '',
    diseaseInput: '',
  });

  const { symptoms, prediction, loading, error, setSymptoms, setPrediction, setLoading, setError, reset } = useStore();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    fetchSymptoms();
  }, []);

  const fetchSymptoms = async () => {
    try {
      const data = await userApi.getSymptoms();
      setSymptoms(data);
    } catch (err) {
      setError('Failed to load symptoms');
    }
  };

  const handleSubmit = async () => {
    if (!isAuthenticated) {
      setError('Please login to continue');
      router.push('/dashboard');
      return;
    }

    if (!formData.name || !formData.age || !formData.gender || Object.keys(formData.selectedSymptoms).length === 0) {
      setError('Please fill all required fields and select at least one symptom');
      return;
    }

    // Validate symptom details
    const hasIncompleteSymptoms = Object.values(formData.selectedSymptoms).some(
      s => !s.severity || !s.duration || !s.onset
    );

    if (hasIncompleteSymptoms) {
      setError('Please complete all details for selected symptoms');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const symptomsArray = Object.entries(formData.selectedSymptoms).map(([id, details]) => ({
        id: parseInt(id),
        severity: details.severity,
        duration: details.duration,
        onset: details.onset
      }));

      const data = await userApi.predict({
        name: formData.name,
        age: parseInt(formData.age),
        gender: formData.gender,
        height: formData.height ? parseFloat(formData.height) : null,
        weight: formData.weight ? parseFloat(formData.weight) : null,
        occupation: formData.occupation,
        symptoms: symptomsArray,
        existing_diseases: formData.existing_diseases,
        allergies: formData.allergies,
        medications: formData.medications,
        family_history: formData.family_history,
        lifestyle: {
          smoking: formData.lifestyle.smoking,
          alcohol: formData.lifestyle.alcohol,
          diet: formData.lifestyle.diet,
          sleep_hours: formData.lifestyle.sleep_hours ? parseInt(formData.lifestyle.sleep_hours) : null,
          exercise_frequency: formData.lifestyle.exercise_frequency,
          stress_level: formData.lifestyle.stress_level ? parseInt(formData.lifestyle.stress_level) : null
        },
        travel_history: formData.travel_history
      });
      setPrediction(data);
    } catch (err) {
      if (err.response?.status === 401) {
        setError('Session expired. Please login again.');
      } else {
        setError(err.response?.data?.message || 'Failed to get prediction');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSymptomToggle = (symptomId) => {
    setFormData(prev => {
      const newSymptoms = { ...prev.selectedSymptoms };
      if (newSymptoms[symptomId]) {
        delete newSymptoms[symptomId];
      } else {
        newSymptoms[symptomId] = {
          severity: 5,
          duration: '',
          onset: 'GRADUAL'
        };
      }
      return { ...prev, selectedSymptoms: newSymptoms };
    });
  };

  const updateSymptomDetail = (symptomId, field, value) => {
    setFormData(prev => ({
      ...prev,
      selectedSymptoms: {
        ...prev.selectedSymptoms,
        [symptomId]: {
          ...prev.selectedSymptoms[symptomId],
          [field]: value
        }
      }
    }));
  };

  const handleReset = () => {
    setFormData({
      name: '',
      age: '',
      gender: '',
      height: '',
      weight: '',
      occupation: '',
      selectedSymptoms: {},
      existing_diseases: [],
      allergies: '',
      medications: '',
      family_history: '',
      lifestyle: {
        smoking: false,
        alcohol: false,
        diet: '',
        sleep_hours: '',
        exercise_frequency: '',
        stress_level: ''
      },
      travel_history: '',
      diseaseInput: '',
    });
    reset();
  };

  const addDisease = () => {
    if (formData.diseaseInput.trim()) {
      setFormData(prev => ({
        ...prev,
        existing_diseases: [...prev.existing_diseases, formData.diseaseInput.trim()],
        diseaseInput: ''
      }));
    }
  };

  const removeDisease = (index) => {
    setFormData(prev => ({
      ...prev,
      existing_diseases: prev.existing_diseases.filter((_, i) => i !== index)
    }));
  };

  const getSeverityColor = (category) => {
    switch (category) {
      case 'NORMAL': return 'bg-green-100 text-green-800 border-green-300';
      case 'MODERATE': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'RISKY': return 'bg-red-100 text-red-800 border-red-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  if (prediction) {
    const { submission, recommendations, additional_info } = prediction;

    return (
      <div className="w-full max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Prediction Results</h1>
          <Button onClick={handleReset} variant="outline">
            New Analysis
          </Button>
        </div>

        {/* Patient Information */}
        <Card className="border-2">
          <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50">
            <CardTitle className="flex items-center gap-2">
              <User className="w-5 h-5" />
              Patient Information
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="grid md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-500">Name</p>
                <p className="font-semibold">{submission.name}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Age</p>
                <p className="font-semibold">{submission.age} years</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Gender</p>
                <p className="font-semibold">
                  {submission.gender === 'M' ? 'Male' : submission.gender === 'F' ? 'Female' : 'Other'}
                </p>
              </div>
              {submission.occupation && (
                <div>
                  <p className="text-sm text-gray-500">Occupation</p>
                  <p className="font-semibold">{submission.occupation}</p>
                </div>
              )}
            </div>
            
            {(submission.height || submission.weight || submission.bmi) && (
              <div className="grid md:grid-cols-3 gap-4 mt-4 pt-4 border-t">
                {submission.height && (
                  <div>
                    <p className="text-sm text-gray-500">Height</p>
                    <p className="font-semibold">{submission.height} cm</p>
                  </div>
                )}
                {submission.weight && (
                  <div>
                    <p className="text-sm text-gray-500">Weight</p>
                    <p className="font-semibold">{submission.weight} kg</p>
                  </div>
                )}
                {submission.bmi && (
                  <div>
                    <p className="text-sm text-gray-500">BMI</p>
                    <p className="font-semibold">{submission.bmi}</p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Symptoms */}
        <Card className="border-2">
          <CardHeader className="bg-gradient-to-r from-purple-50 to-pink-50">
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              Reported Symptoms
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="grid md:grid-cols-2 gap-4">
              {submission.symptoms.map((symptom) => (
                <div key={symptom.id} className="p-4 border rounded-lg bg-gray-50">
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-semibold text-lg">{symptom.name}</h4>
                    <Badge variant="outline">{symptom.severity}/10</Badge>
                  </div>
                  <div className="space-y-1 text-sm text-gray-600">
                    <p><span className="font-medium">Duration:</span> {symptom.duration}</p>
                    <p><span className="font-medium">Onset:</span> {symptom.onset}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Medical Analysis */}
        <Card className="border-2">
          <CardHeader className="bg-gradient-to-r from-indigo-50 to-purple-50">
            <CardTitle className="flex items-center gap-2">
              <Stethoscope className="w-5 h-5" />
              Medical Analysis
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6 space-y-4">
            {/* Primary Prediction */}
            <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border-2 border-blue-200">
              <p className="text-sm text-gray-600 mb-2">Primary Diagnosis</p>
              <p className="text-2xl font-bold text-blue-900">{submission.primary_prediction}</p>
            </div>

            {/* All Predictions */}
            {submission.predicted_diseases && submission.predicted_diseases.length > 0 && (
              <div>
                <h4 className="font-semibold mb-3">Possible Conditions</h4>
                <div className="space-y-2">
                  {submission.predicted_diseases.map((disease, index) => (
                    <div key={disease.id} className="flex items-center justify-between p-3 bg-white border rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                          index === 0 ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
                        }`}>
                          {index + 1}
                        </div>
                        <span className="font-medium">{disease.name}</span>
                      </div>
                      <Badge variant={index === 0 ? 'default' : 'secondary'}>
                        {disease.confidence_score.toFixed(2)}%
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Scores */}
            <div className="grid md:grid-cols-2 gap-4">
              <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <p className="text-sm text-gray-600 mb-1">Severity Score</p>
                <p className="text-3xl font-bold text-blue-700">{submission.severity_score}%</p>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                <p className="text-sm text-gray-600 mb-1">Severity Category</p>
                <Badge className={`${getSeverityColor(submission.severity_category)} border text-lg px-3 py-1`}>
                  {submission.severity_category}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Lifestyle Information */}
        {submission.lifestyle && (
          <Card className="border-2">
            <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50">
              <CardTitle className="flex items-center gap-2">
                <Heart className="w-5 h-5" />
                Lifestyle Information
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid md:grid-cols-3 gap-4">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${submission.lifestyle.smoking ? 'bg-red-500' : 'bg-green-500'}`} />
                  <span>Smoking: {submission.lifestyle.smoking ? 'Yes' : 'No'}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${submission.lifestyle.alcohol ? 'bg-red-500' : 'bg-green-500'}`} />
                  <span>Alcohol: {submission.lifestyle.alcohol ? 'Yes' : 'No'}</span>
                </div>
                {submission.lifestyle.diet && (
                  <div>
                    <span className="font-medium">Diet:</span> {submission.lifestyle.diet}
                  </div>
                )}
                {submission.lifestyle.sleep_hours && (
                  <div>
                    <span className="font-medium">Sleep:</span> {submission.lifestyle.sleep_hours} hours
                  </div>
                )}
                {submission.lifestyle.exercise_frequency && (
                  <div>
                    <span className="font-medium">Exercise:</span> {submission.lifestyle.exercise_frequency}
                  </div>
                )}
                {submission.lifestyle.stress_level && (
                  <div>
                    <span className="font-medium">Stress Level:</span> {submission.lifestyle.stress_level}/10
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Recommendations */}
        <Card className="border-2">
          <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50">
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5" />
              Recommendations
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6 space-y-6">
            {recommendations.lifestyle_tips && recommendations.lifestyle_tips.length > 0 && (
              <div>
                <h3 className="font-semibold text-lg mb-3 flex items-center gap-2">
                  <Dumbbell className="w-5 h-5 text-green-600" />
                  Lifestyle Tips
                </h3>
                <ul className="bg-green-50 p-4 rounded-lg border border-green-200 space-y-2">
                  {recommendations.lifestyle_tips.map((tip, index) => (
                    <li key={index} className="flex gap-2 text-sm text-gray-700">
                      <span className="text-green-600 font-bold">•</span>
                      <span>{tip}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {recommendations.diet_advice && recommendations.diet_advice.length > 0 && (
              <div>
                <h3 className="font-semibold text-lg mb-3 flex items-center gap-2">
                  <Utensils className="w-5 h-5 text-orange-600" />
                  Diet Advice
                </h3>
                <ul className="bg-orange-50 p-4 rounded-lg border border-orange-200 space-y-2">
                  {recommendations.diet_advice.map((advice, index) => (
                    <li key={index} className="flex gap-2 text-sm text-gray-700">
                      <span className="text-orange-600 font-bold">•</span>
                      <span>{advice}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {recommendations.medical_advice && recommendations.medical_advice.length > 0 && (
              <div>
                <h3 className="font-semibold text-lg mb-3 flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-red-600" />
                  Medical Advice
                </h3>
                <ul className="bg-red-50 p-4 rounded-lg border border-red-200 space-y-2">
                  {recommendations.medical_advice.map((advice, index) => (
                    <li key={index} className="flex gap-2 text-sm text-gray-700">
                      <span className="text-red-600 font-bold">•</span>
                      <span>{advice}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Additional Info */}
        {additional_info && (
          <Card className="border-2">
            <CardHeader className="bg-gradient-to-r from-yellow-50 to-amber-50">
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                Additional Information
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6 space-y-4">
              {additional_info.severity_interpretation && (
                <div>
                  <h4 className="font-semibold mb-2">Severity Interpretation</h4>
                  <p className="text-gray-700">{additional_info.severity_interpretation}</p>
                </div>
              )}
              {additional_info.next_steps && (
                <div>
                  <h4 className="font-semibold mb-2">Next Steps</h4>
                  <p className="text-gray-700">{additional_info.next_steps}</p>
                </div>
              )}
              {additional_info.disclaimer && (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{additional_info.disclaimer}</AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    );
  }

  return (
    <div className="w-full max-w-6xl mx-auto">
      <Card className="border-2 shadow-lg">
        <CardHeader >
          <CardTitle className="text-2xl">Medical Prediction System</CardTitle>
          <CardDescription >
            Enter comprehensive patient details for AI-powered health analysis
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="space-y-6">
            {/* Basic Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold border-b pb-2">Basic Information</h3>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">Full Name *</Label>
                  <Input
                    id="name"
                    placeholder="John Doe"
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="age">Age *</Label>
                  <Input
                    id="age"
                    type="number"
                    placeholder="30"
                    value={formData.age}
                    onChange={(e) => setFormData(prev => ({ ...prev, age: e.target.value }))}
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="gender">Gender *</Label>
                  <Select value={formData.gender} onValueChange={(value) => setFormData(prev => ({ ...prev, gender: value }))}>
                    <SelectTrigger className="mt-1">
                      <SelectValue placeholder="Select gender" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="M">Male</SelectItem>
                      <SelectItem value="F">Female</SelectItem>
                      <SelectItem value="O">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="occupation">Occupation</Label>
                  <Input
                    id="occupation"
                    placeholder="Software Engineer"
                    value={formData.occupation}
                    onChange={(e) => setFormData(prev => ({ ...prev, occupation: e.target.value }))}
                    className="mt-1"
                  />
                </div>
              </div>
            </div>

            {/* Physical Metrics */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold border-b pb-2">Physical Metrics</h3>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="height">Height (cm)</Label>
                  <Input
                    id="height"
                    type="number"
                    placeholder="175"
                    value={formData.height}
                    onChange={(e) => setFormData(prev => ({ ...prev, height: e.target.value }))}
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="weight">Weight (kg)</Label>
                  <Input
                    id="weight"
                    type="number"
                    placeholder="70"
                    value={formData.weight}
                    onChange={(e) => setFormData(prev => ({ ...prev, weight: e.target.value }))}
                    className="mt-1"
                  />
                </div>
              </div>
            </div>

            {/* Symptoms */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold border-b pb-2">Symptoms *</h3>
              <Card className="p-4 max-h-96 overflow-y-auto">
                {symptoms.length === 0 ? (
                  <p className="text-sm text-gray-500">Loading symptoms...</p>
                ) : (
                  <div className="space-y-4">
                    {symptoms.map((symptom) => (
                      <div key={symptom.id} className="border rounded-lg p-4">
                        <div className="flex items-start space-x-3">
                          <Checkbox
                            id={`symptom-${symptom.id}`}
                            checked={!!formData.selectedSymptoms[symptom.id]}
                            onCheckedChange={() => handleSymptomToggle(symptom.id)}
                          />
                          <div className="flex-1">
                            <label htmlFor={`symptom-${symptom.id}`} className="font-medium cursor-pointer">
                              {symptom.name}
                            </label>
                            {symptom.description && (
                              <p className="text-xs text-gray-500 mt-1">{symptom.description}</p>
                            )}
                            
                            {formData.selectedSymptoms[symptom.id] && (
                              <div className="mt-3 space-y-3 bg-gray-50 p-3 rounded">
                                <div>
                                  <Label className="text-xs">Severity (1-10)</Label>
                                  <Input
                                    type="number"
                                    min="1"
                                    max="10"
                                    value={formData.selectedSymptoms[symptom.id].severity}
                                    onChange={(e) => updateSymptomDetail(symptom.id, 'severity', parseInt(e.target.value))}
                                    className="mt-1"
                                  />
                                </div>
                                <div>
                                  <Label className="text-xs">Duration</Label>
                                  <Input
                                    placeholder="e.g., 3 days, 1 week"
                                    value={formData.selectedSymptoms[symptom.id].duration}
                                    onChange={(e) => updateSymptomDetail(symptom.id, 'duration', e.target.value)}
                                    className="mt-1"
                                  />
                                </div>
                                <div>
                                  <Label className="text-xs">Onset</Label>
                                  <Select
                                    value={formData.selectedSymptoms[symptom.id].onset}
                                    onValueChange={(value) => updateSymptomDetail(symptom.id, 'onset', value)}
                                  >
                                    <SelectTrigger className="mt-1">
                                      <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                      <SelectItem value="SUDDEN">Sudden</SelectItem>
                                      <SelectItem value="GRADUAL">Gradual</SelectItem>
                                    </SelectContent>
                                  </Select>
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
              {Object.keys(formData.selectedSymptoms).length > 0 && (
                <p className="text-sm text-gray-600">
                  {Object.keys(formData.selectedSymptoms).length} symptom(s) selected
                </p>
              )}
            </div>

            {/* Medical History */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold border-b pb-2">Medical History</h3>
              <div className="space-y-4">
                <div>
                  <Label>Existing Diseases</Label>
                  <div className="flex gap-2 mt-1">
                    <Input
                      placeholder="e.g., Asthma, Diabetes"
                      value={formData.diseaseInput}
                      onChange={(e) => setFormData(prev => ({ ...prev, diseaseInput: e.target.value }))}
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addDisease())}
                    />
                    <Button type="button" onClick={addDisease} variant="outline">Add</Button>
                  </div>
                  {formData.existing_diseases.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {formData.existing_diseases.map((disease, index) => (
                        <Badge key={index} variant="secondary" className="px-2 py-1">
                          {disease}
                          <button
                            onClick={() => removeDisease(index)}
                            className="ml-2 text-red-500 hover:text-red-700"
                          >
                            ×
                          </button>
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
                <div>
                  <Label htmlFor="allergies">Allergies</Label>
                  <Input
                    id="allergies"
                    placeholder="Peanuts, Penicillin, etc."
                    value={formData.allergies}
                    onChange={(e) => setFormData(prev => ({ ...prev, allergies: e.target.value }))}
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="medications">Current Medications</Label>
                  <Input
                    id="medications"
                    placeholder="Paracetamol, Aspirin, etc."
                    value={formData.medications}
                    onChange={(e) => setFormData(prev => ({ ...prev, medications: e.target.value }))}
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="family_history">Family History</Label>
                  <Input
                    id="family_history"
                    placeholder="Heart Disease, Cancer, etc."
                    value={formData.family_history}
                    onChange={(e) => setFormData(prev => ({ ...prev, family_history: e.target.value }))}
                    className="mt-1"
                  />
                </div>
              </div>
            </div>

            {/* Lifestyle */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold border-b pb-2">Lifestyle Information</h3>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="smoking"
                    checked={formData.lifestyle.smoking}
                    onCheckedChange={(checked) => setFormData(prev => ({
                      ...prev,
                      lifestyle: { ...prev.lifestyle, smoking: checked }
                    }))}
                  />
                  <Label htmlFor="smoking" className="cursor-pointer">Smoking</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="alcohol"
                    checked={formData.lifestyle.alcohol}
                    onCheckedChange={(checked) => setFormData(prev => ({
                      ...prev,
                      lifestyle: { ...prev.lifestyle, alcohol: checked }
                    }))}
                  />
                  <Label htmlFor="alcohol" className="cursor-pointer">Alcohol Consumption</Label>
                </div>
                <div>
                  <Label htmlFor="diet">Diet Type</Label>
                  <Select
                    value={formData.lifestyle.diet}
                    onValueChange={(value) => setFormData(prev => ({
                      ...prev,
                      lifestyle: { ...prev.lifestyle, diet: value }
                    }))}
                  >
                    <SelectTrigger className="mt-1">
                      <SelectValue placeholder="Select diet type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="VEG">Vegetarian</SelectItem>
                      <SelectItem value="NON_VEG">Non-Vegetarian</SelectItem>
                      <SelectItem value="VEGAN">Vegan</SelectItem>
                      <SelectItem value="MIXED">Mixed</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="sleep_hours">Sleep Hours (per day)</Label>
                  <Input
                    id="sleep_hours"
                    type="number"
                    min="0"
                    max="24"
                    placeholder="7"
                    value={formData.lifestyle.sleep_hours}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      lifestyle: { ...prev.lifestyle, sleep_hours: e.target.value }
                    }))}
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="exercise_frequency">Exercise Frequency</Label>
                  <Input
                    id="exercise_frequency"
                    placeholder="3 times/week"
                    value={formData.lifestyle.exercise_frequency}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      lifestyle: { ...prev.lifestyle, exercise_frequency: e.target.value }
                    }))}
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="stress_level">Stress Level (1-10)</Label>
                  <Input
                    id="stress_level"
                    type="number"
                    min="1"
                    max="10"
                    placeholder="5"
                    value={formData.lifestyle.stress_level}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      lifestyle: { ...prev.lifestyle, stress_level: e.target.value }
                    }))}
                    className="mt-1"
                  />
                </div>
              </div>
            </div>

            {/* Travel History */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold border-b pb-2">Additional Information</h3>
              <div>
                <Label htmlFor="travel_history">Travel History</Label>
                <Input
                  id="travel_history"
                  placeholder="Delhi to Kerala, International travel, etc."
                  value={formData.travel_history}
                  onChange={(e) => setFormData(prev => ({ ...prev, travel_history: e.target.value }))}
                  className="mt-1"
                />
              </div>
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="flex gap-3">
              <Button onClick={handleSubmit} className="flex-1" disabled={loading}>
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  'Get Prediction'
                )}
              </Button>
              <Button variant="outline" onClick={handleReset}>
                Reset
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Alert className="mt-6">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription className="text-xs">
          This system provides AI-based predictions for educational purposes only. 
          Always consult qualified healthcare professionals for medical decisions.
        </AlertDescription>
      </Alert>
    </div>
  );
}